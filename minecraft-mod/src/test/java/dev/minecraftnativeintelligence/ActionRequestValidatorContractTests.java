package dev.minecraftnativeintelligence;

import com.google.gson.JsonParser;
import java.util.Map;
import java.util.Set;

/** Dependency-free executable contract checks; these do not start Minecraft. */
public final class ActionRequestValidatorContractTests {
    private ActionRequestValidatorContractTests() {}

    public static void main(String[] args) {
        var valid = request("{\"type\":\"move\",\"forward\":1,\"strafe\":0}");
        equal("duplicate_request_id", ActionRequestValidator.validate(valid, contextWithSeenId()).reasonCode(), "duplicate ID");
        checkEveryActionVariant();
        equal("malformed_request", validateRaw(envelope("-1", "{\"type\":\"jump\"}")).reasonCode(), "negative observation sequence");
        equal("malformed_request", validateRaw(envelope("999999999999999999999999999999", "{\"type\":\"jump\"}")).reasonCode(), "overflow observation sequence");
        equal("malformed_request", validateRaw(envelope("4", "{\"type\":\"jump\"}").replace("\"session_epoch\":3", "\"session_epoch\":-1")).reasonCode(), "negative session epoch");
        equal("malformed_request", validateRaw(envelope("4", "{\"type\":\"jump\"}").replace("\"action\":", "\"deadline_game_tick\":-1,\"action\":")).reasonCode(), "negative deadline");
        equal("invalid_action_shape", validateRaw(envelope("4", "{\"type\":\"interact\",\"target_block\":{\"x\":0,\"y\":64,\"z\":0}}" )).reasonCode(), "missing interact target kind");
        equal("target_out_of_reach", validateRaw(envelope("4", "{\"type\":\"attack\",\"target_entity_id\":\"mob-1\"}")).reasonCode(), "unreachable attack");
        equal("unsupported_capability", validateRaw(envelope("4", "{\"type\":\"eat\",\"hand\":\"main\"}")).reasonCode(), "unsupported action capability");
        equal("inventory_precondition_failed", validateRaw(envelope("4", "{\"type\":\"drop\",\"slot\":0,\"count\":1,\"whole_stack\":true}")).reasonCode(), "whole-stack count mismatch");
        equal("malformed_request", ActionRequestValidator.validate("{", context()).reasonCode(), "malformed JSON");
        System.out.println("ActionRequestValidator contract checks passed (26 cases)");
    }

    private static void checkEveryActionVariant() {
        String[] actions = {
                "{\"type\":\"move\",\"forward\":1,\"strafe\":0}",
                "{\"type\":\"look\",\"yaw_degrees\":180,\"pitch_degrees\":0}",
                "{\"type\":\"jump\"}",
                "{\"type\":\"attack\",\"target_entity_id\":\"mob-1\"}",
                "{\"type\":\"mine\",\"target\":{\"x\":0,\"y\":64,\"z\":0}}",
                "{\"type\":\"place\",\"target\":{\"x\":0,\"y\":64,\"z\":0},\"face\":\"up\"}",
                "{\"type\":\"interact\",\"target_kind\":\"block\",\"target_block\":{\"x\":0,\"y\":64,\"z\":0}}",
                "{\"type\":\"interact\",\"target_kind\":\"entity\",\"target_entity_id\":\"mob-1\"}",
                "{\"type\":\"select_slot\",\"hotbar_slot\":0}",
                "{\"type\":\"drop\",\"slot\":0,\"count\":1}",
                "{\"type\":\"pickup\",\"item_entity_id\":\"item-1\"}",
                "{\"type\":\"craft\",\"recipe_id\":\"minecraft:planks\",\"times\":2}",
                "{\"type\":\"equip\",\"slot\":\"head\",\"inventory_slot\":0}",
                "{\"type\":\"eat\",\"hand\":\"main\"}",
                "{\"type\":\"chat\",\"message\":\"hello\"}",
                "{\"type\":\"cancel\",\"target_request_id\":\"active-1\"}"
        };
        for (String action : actions) {
            equal(true, ActionRequestValidator.validate(request(action), fullContext()).accepted(), "valid action " + action);
        }
    }

    private static ActionRequestValidator.Result validateRaw(String request) {
        return ActionRequestValidator.validate(request, context());
    }

    private static String envelope(String sequence, String action) {
        return "{\"schema_version\":\"action-request.v0\",\"agent_id\":\"agent-1\",\"session_epoch\":3,"
                + "\"request_id\":\"req-1\",\"based_on_observation_seq\":" + sequence
                + ",\"trace_id\":\"trace-1\",\"action\":" + action + "}";
    }

    private static com.google.gson.JsonObject request(String action) {
        return JsonParser.parseString(envelope("4", action)).getAsJsonObject();
    }

    private static ActionValidationContext context() {
        return new ActionValidationContext("agent-1", 3, 4, 100, 2, 41, true,
                Set.of(ActionValidationContext.actionCapability("move"), ActionValidationContext.actionCapability("jump"),
                        ActionValidationContext.actionCapability("attack"), ActionValidationContext.actionCapability("drop")),
                Set.of("move", "jump", "attack", "drop"), Set.of("mob-1"), Set.of(), Set.of("0,64,0"),
                Set.of(), Set.of(), Set.of(), Set.of(), Set.of(), Set.of(),
                Map.of(0, new ActionValidationContext.ItemState("minecraft:stone", 2, false, false, "")), Map.of());
    }

    private static ActionValidationContext contextWithSeenId() {
        ActionValidationContext base = context();
        return new ActionValidationContext(base.agentId(), base.sessionEpoch(), base.observationSequence(), base.gameTick(),
                base.maxObservationLag(), base.inventorySize(), base.hungry(), base.supportedCapabilities(), base.permittedActions(),
                base.visibleEntityRefs(), base.reachableEntityRefs(), base.visibleBlockRefs(), base.reachableBlockRefs(),
                base.mineableBlockRefs(), base.availableRecipeIds(), base.activeRequestIds(), Set.of("req-1"),
                base.blockedCooldowns(), base.inventory(), base.heldItems());
    }

    private static ActionValidationContext fullContext() {
        Set<String> actions = Set.of("move", "look", "jump", "attack", "mine", "place", "interact", "select_slot",
                "drop", "pickup", "craft", "equip", "eat", "chat", "cancel");
        Set<String> capabilities = actions.stream().map(ActionValidationContext::actionCapability).collect(java.util.stream.Collectors.toSet());
        return new ActionValidationContext("agent-1", 3, 4, 100, 2, 41, true, capabilities, actions,
                Set.of("mob-1", "item-1"), Set.of("mob-1", "item-1"), Set.of("0,64,0"), Set.of("0,64,0"),
                Set.of("0,64,0"), Set.of("minecraft:planks"), Set.of("active-1"), Set.of(), Set.of(),
                Map.of(0, new ActionValidationContext.ItemState("minecraft:helmet", 2, true, true, "head")),
                Map.of("main", new ActionValidationContext.ItemState("minecraft:bread", 2, true, true, "")));
    }

    private static void equal(Object expected, Object actual, String label) {
        if (!expected.equals(actual)) throw new AssertionError(label + ": expected " + expected + ", got " + actual);
    }
}
