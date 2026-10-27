package dev.minecraftnativeintelligence;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.util.Set;

/** Pure fail-closed validation. This class never mutates a player or world. */
public final class ActionRequestValidator {
    private static final Set<String> ENVELOPE_FIELDS = Set.of(
            "schema_version", "agent_id", "session_epoch", "request_id", "based_on_observation_seq",
            "trace_id", "deadline_game_tick", "action");

    private ActionRequestValidator() {}

    public record Result(boolean accepted, String reasonCode, String requestId, String traceId) {
        private static Result accept(String requestId, String traceId) {
            return new Result(true, "accepted", requestId, traceId);
        }

        private static Result reject(String reasonCode, String requestId, String traceId) {
            return new Result(false, reasonCode, requestId, traceId);
        }
    }

    public static Result validate(String json, ActionValidationContext context) {
        final JsonElement parsed;
        try {
            parsed = JsonParser.parseString(json);
        } catch (RuntimeException malformed) {
            return Result.reject("malformed_request", "", "");
        }
        if (parsed == null || !parsed.isJsonObject()) {
            return Result.reject("malformed_request", "", "");
        }
        return validate(parsed.getAsJsonObject(), context);
    }

    public static Result validate(JsonObject request, ActionValidationContext context) {
        if (request == null || !hasOnly(request, ENVELOPE_FIELDS)
                || !hasRequired(request, "schema_version", "agent_id", "session_epoch", "request_id",
                        "based_on_observation_seq", "trace_id", "action")) {
            return Result.reject("malformed_request", fieldString(request, "request_id"), fieldString(request, "trace_id"));
        }
        String requestId = fieldString(request, "request_id");
        String traceId = fieldString(request, "trace_id");
        if (!"action-request.v0".equals(fieldString(request, "schema_version"))) {
            return Result.reject("unsupported_schema_version", requestId, traceId);
        }
        if (!context.agentId().equals(fieldString(request, "agent_id"))) {
            return Result.reject("unauthorized_agent", requestId, traceId);
        }
        if (!nonEmptyString(request, "agent_id", 128) || !nonEmptyString(request, "request_id", 128)
                || !nonEmptyString(request, "trace_id", 128)) {
            return Result.reject("malformed_request", requestId, traceId);
        }
        if (!longInteger(request.get("session_epoch")) || request.get("session_epoch").getAsLong() < 0) {
            return Result.reject("malformed_request", requestId, traceId);
        }
        if (request.get("session_epoch").getAsLong() != context.sessionEpoch()) {
            return Result.reject("stale_session", requestId, traceId);
        }
        if (context.seenRequestIds().contains(requestId)) {
            return Result.reject("duplicate_request_id", requestId, traceId);
        }
        if (!longInteger(request.get("based_on_observation_seq"))) {
            return Result.reject("malformed_request", requestId, traceId);
        }
        long basedOnSequence = request.get("based_on_observation_seq").getAsLong();
        if (basedOnSequence < 0) {
            return Result.reject("malformed_request", requestId, traceId);
        }
        if (basedOnSequence > context.observationSequence()) {
            return Result.reject("future_observation", requestId, traceId);
        }
        if (context.observationSequence() - basedOnSequence > context.maxObservationLag()) {
            return Result.reject("stale_observation", requestId, traceId);
        }
        if (request.has("deadline_game_tick")) {
            if (!longInteger(request.get("deadline_game_tick")) || request.get("deadline_game_tick").getAsLong() < 0) {
                return Result.reject("malformed_request", requestId, traceId);
            }
            if (context.gameTick() > request.get("deadline_game_tick").getAsLong()) {
                return Result.reject("deadline_expired", requestId, traceId);
            }
        }

        JsonElement actionElement = request.get("action");
        if (actionElement == null || !actionElement.isJsonObject()) {
            return Result.reject("invalid_action_shape", requestId, traceId);
        }
        JsonObject action = actionElement.getAsJsonObject();
        String type = fieldString(action, "type");
        if (type.isBlank() || !validateShape(action, type)) {
            return Result.reject("invalid_action_shape", requestId, traceId);
        }
        if (!context.supportedCapabilities().contains(ActionValidationContext.actionCapability(type))) {
            return Result.reject("unsupported_capability", requestId, traceId);
        }
        if (!context.permittedActions().contains(type)) {
            return Result.reject("permission_denied", requestId, traceId);
        }
        if (context.blockedCooldowns().contains(type)) {
            return Result.reject("cooldown_active", requestId, traceId);
        }
        Result domainResult = validateMinecraftPreconditions(action, type, requestId, traceId, context);
        return domainResult == null ? Result.accept(requestId, traceId) : domainResult;
    }

    private static Result validateMinecraftPreconditions(
            JsonObject action, String type, String requestId, String traceId, ActionValidationContext context) {
        switch (type) {
            case "attack", "interact" -> {
                if ("block".equals(fieldString(action, "target_kind"))) {
                    return validateBlockRef(action.get("target_block"), type, requestId, traceId, context);
                }
                if ("entity".equals(fieldString(action, "target_kind")) || type.equals("attack")) {
                    String ref = fieldString(action, "target_entity_id");
                    return validateEntityRef(ref, requestId, traceId, context);
                }
                return Result.reject("invalid_action_shape", requestId, traceId);
            }
            case "mine", "place" -> {
                Result target = validateBlockRef(action.get("target"), type, requestId, traceId, context);
                if (target != null) {
                    return target;
                }
                if (type.equals("mine") && !context.mineableBlockRefs().contains(blockRef(action.get("target")))) {
                    return Result.reject("block_not_mineable", requestId, traceId);
                }
                if (type.equals("place")) {
                    String hand = action.has("hand") ? fieldString(action, "hand") : "main";
                    ActionValidationContext.ItemState held = context.heldItems().get(hand);
                    if (held == null || held.count() == 0 || !held.placeable()) {
                        return Result.reject("inventory_precondition_failed", requestId, traceId);
                    }
                }
            }
            case "pickup" -> {
                return validateEntityRef(fieldString(action, "item_entity_id"), requestId, traceId, context);
            }
            case "select_slot" -> {
                int slot = action.get("hotbar_slot").getAsInt();
                if (slot >= context.inventorySize()) {
                    return Result.reject("inventory_precondition_failed", requestId, traceId);
                }
            }
            case "drop" -> {
                int slot = action.get("slot").getAsInt();
                int count = action.get("count").getAsInt();
                ActionValidationContext.ItemState item = context.inventory().get(slot);
                boolean wholeStack = action.has("whole_stack") && action.get("whole_stack").getAsBoolean();
                if (slot >= context.inventorySize() || item == null || item.count() < count
                        || (wholeStack && item.count() != count)) {
                    return Result.reject("inventory_precondition_failed", requestId, traceId);
                }
            }
            case "craft" -> {
                if (!context.availableRecipeIds().contains(fieldString(action, "recipe_id"))) {
                    return Result.reject("recipe_unavailable", requestId, traceId);
                }
            }
            case "equip" -> {
                int slot = action.get("inventory_slot").getAsInt();
                ActionValidationContext.ItemState item = context.inventory().get(slot);
                if (slot >= context.inventorySize() || item == null
                        || !fieldString(action, "slot").equals(item.equipmentSlot())) {
                    return Result.reject("inventory_precondition_failed", requestId, traceId);
                }
            }
            case "eat" -> {
                String hand = fieldString(action, "hand");
                ActionValidationContext.ItemState held = context.heldItems().get(hand);
                if (!context.hungry() || held == null || held.count() == 0 || !held.edible()) {
                    return Result.reject("inventory_precondition_failed", requestId, traceId);
                }
            }
            case "cancel" -> {
                if (!context.activeRequestIds().contains(fieldString(action, "target_request_id"))) {
                    return Result.reject("cancel_target_not_active", requestId, traceId);
                }
            }
            default -> {
                // Pure controls and communication have no additional world precondition here.
            }
        }
        return null;
    }

    private static Result validateEntityRef(
            String ref, String requestId, String traceId, ActionValidationContext context) {
        if (!context.visibleEntityRefs().contains(ref)) {
            return Result.reject("target_not_observed", requestId, traceId);
        }
        if (!context.reachableEntityRefs().contains(ref)) {
            return Result.reject("target_out_of_reach", requestId, traceId);
        }
        return null;
    }

    private static Result validateBlockRef(
            JsonElement target, String type, String requestId, String traceId, ActionValidationContext context) {
        if (target == null || !target.isJsonObject()) {
            return Result.reject("invalid_action_shape", requestId, traceId);
        }
        String ref = blockRef(target);
        if (!context.visibleBlockRefs().contains(ref)) {
            return Result.reject("target_not_observed", requestId, traceId);
        }
        if (!context.reachableBlockRefs().contains(ref)) {
            return Result.reject("target_out_of_reach", requestId, traceId);
        }
        return null;
    }

    private static String blockRef(JsonElement target) {
        JsonObject pos = target.getAsJsonObject();
        return pos.get("x").getAsInt() + "," + pos.get("y").getAsInt() + "," + pos.get("z").getAsInt();
    }

    private static boolean validateShape(JsonObject action, String type) {
        Set<String> allowed;
        Set<String> required;
        switch (type) {
            case "move" -> { allowed = Set.of("type", "forward", "strafe", "sprint", "sneak", "duration_ticks"); required = Set.of("type", "forward", "strafe"); }
            case "look" -> { allowed = Set.of("type", "yaw_degrees", "pitch_degrees"); required = allowed; }
            case "jump" -> { allowed = Set.of("type", "hold_ticks"); required = Set.of("type"); }
            case "attack" -> { allowed = Set.of("type", "target_entity_id"); required = allowed; }
            case "mine" -> { allowed = Set.of("type", "target", "face"); required = Set.of("type", "target"); }
            case "place" -> { allowed = Set.of("type", "target", "face", "hand"); required = Set.of("type", "target", "face"); }
            case "select_slot" -> { allowed = Set.of("type", "hotbar_slot"); required = allowed; }
            case "drop" -> { allowed = Set.of("type", "slot", "count", "whole_stack"); required = Set.of("type", "slot", "count"); }
            case "pickup" -> { allowed = Set.of("type", "item_entity_id"); required = allowed; }
            case "craft" -> { allowed = Set.of("type", "recipe_id", "times"); required = Set.of("type", "recipe_id"); }
            case "equip" -> { allowed = Set.of("type", "slot", "inventory_slot"); required = allowed; }
            case "eat" -> { allowed = Set.of("type", "hand"); required = allowed; }
            case "chat" -> { allowed = Set.of("type", "message"); required = allowed; }
            case "cancel" -> { allowed = Set.of("type", "target_request_id"); required = allowed; }
            case "interact" -> {
                String kind = fieldString(action, "target_kind");
                if (kind.equals("block")) {
                    allowed = Set.of("type", "target_kind", "target_block", "hand");
                    required = Set.of("type", "target_kind", "target_block");
                } else if (kind.equals("entity")) {
                    allowed = Set.of("type", "target_kind", "target_entity_id", "hand");
                    required = Set.of("type", "target_kind", "target_entity_id");
                } else {
                    return false;
                }
            }
            default -> { return false; }
        }
        if (!hasOnly(action, allowed) || !hasRequired(action, required.toArray(String[]::new))) {
            return false;
        }
        return validateValues(action, type);
    }

    private static boolean validateValues(JsonObject action, String type) {
        return switch (type) {
            case "move" -> numberRange(action, "forward", -1, 1) && numberRange(action, "strafe", -1, 1)
                    && optionalBoolean(action, "sprint") && optionalBoolean(action, "sneak")
                    && optionalIntRange(action, "duration_ticks", 1, 20);
            case "look" -> number(action, "yaw_degrees") && numberRange(action, "pitch_degrees", -90, 90);
            case "jump" -> optionalIntRange(action, "hold_ticks", 1, 20);
            case "attack" -> nonEmptyString(action, "target_entity_id", 128);
            case "mine" -> validBlock(action.get("target")) && optionalEnum(action, "face", "down", "up", "north", "south", "west", "east");
            case "place" -> validBlock(action.get("target")) && enumValue(action, "face", "down", "up", "north", "south", "west", "east")
                    && optionalEnum(action, "hand", "main", "off");
            case "interact" -> ("block".equals(fieldString(action, "target_kind"))
                    ? validBlock(action.get("target_block"))
                    : nonEmptyString(action, "target_entity_id", 128)) && optionalEnum(action, "hand", "main", "off");
            case "select_slot" -> intRange(action, "hotbar_slot", 0, 8);
            case "drop" -> intRange(action, "slot", 0, Integer.MAX_VALUE) && intRange(action, "count", 1, Integer.MAX_VALUE)
                    && optionalBoolean(action, "whole_stack");
            case "pickup" -> nonEmptyString(action, "item_entity_id", 128);
            case "craft" -> nonEmptyString(action, "recipe_id", 256) && optionalIntRange(action, "times", 1, 64);
            case "equip" -> enumValue(action, "slot", "head", "chest", "legs", "feet", "off_hand")
                    && intRange(action, "inventory_slot", 0, Integer.MAX_VALUE);
            case "eat" -> enumValue(action, "hand", "main", "off");
            case "chat" -> nonEmptyString(action, "message", 256);
            case "cancel" -> nonEmptyString(action, "target_request_id", 128);
            default -> false;
        };
    }

    private static boolean validBlock(JsonElement value) {
        if (value == null || !value.isJsonObject()) return false;
        JsonObject block = value.getAsJsonObject();
        return hasOnly(block, Set.of("x", "y", "z")) && hasRequired(block, "x", "y", "z")
                && integer(block, "x") && integer(block, "y") && integer(block, "z");
    }

    private static boolean hasOnly(JsonObject object, Set<String> allowed) {
        for (String key : object.keySet()) if (!allowed.contains(key)) return false;
        return true;
    }

    private static boolean hasRequired(JsonObject object, String... required) {
        for (String key : required) if (!object.has(key) || object.get(key).isJsonNull()) return false;
        return true;
    }

    private static String fieldString(JsonObject object, String key) {
        if (object == null || !object.has(key) || !object.get(key).isJsonPrimitive()
                || !object.get(key).getAsJsonPrimitive().isString()) return "";
        return object.get(key).getAsString();
    }

    private static boolean nonEmptyString(JsonObject object, String key, int max) {
        String value = fieldString(object, key);
        return !value.isBlank() && value.length() <= max;
    }

    private static boolean integer(JsonObject object, String key) {
        if (!object.has(key) || !isInteger(object.get(key))) return false;
        try {
            object.get(key).getAsBigDecimal().intValueExact();
            return true;
        } catch (ArithmeticException | NumberFormatException invalid) {
            return false;
        }
    }

    private static boolean isInteger(JsonElement value) {
        if (value == null || !value.isJsonPrimitive() || !value.getAsJsonPrimitive().isNumber()) return false;
        try {
            value.getAsBigDecimal().toBigIntegerExact();
            return true;
        } catch (ArithmeticException | NumberFormatException invalid) {
            return false;
        }
    }

    private static boolean longInteger(JsonElement value) {
        if (!isInteger(value)) return false;
        try {
            value.getAsBigDecimal().longValueExact();
            return true;
        } catch (ArithmeticException | NumberFormatException invalid) {
            return false;
        }
    }

    private static boolean intRange(JsonObject object, String key, int min, int max) {
        if (!integer(object, key)) return false;
        long value = object.get(key).getAsLong();
        return value >= min && value <= max;
    }

    private static boolean optionalIntRange(JsonObject object, String key, int min, int max) {
        return !object.has(key) || intRange(object, key, min, max);
    }

    private static boolean number(JsonObject object, String key) {
        return object.has(key) && object.get(key).isJsonPrimitive() && object.get(key).getAsJsonPrimitive().isNumber()
                && Double.isFinite(object.get(key).getAsDouble());
    }

    private static boolean numberRange(JsonObject object, String key, double min, double max) {
        return number(object, key) && object.get(key).getAsDouble() >= min && object.get(key).getAsDouble() <= max;
    }

    private static boolean optionalBoolean(JsonObject object, String key) {
        return !object.has(key) || (object.get(key).isJsonPrimitive() && object.get(key).getAsJsonPrimitive().isBoolean());
    }

    private static boolean enumValue(JsonObject object, String key, String... allowed) {
        String value = fieldString(object, key);
        for (String candidate : allowed) if (candidate.equals(value)) return true;
        return false;
    }

    private static boolean optionalEnum(JsonObject object, String key, String... allowed) {
        return !object.has(key) || enumValue(object, key, allowed);
    }
}
