package dev.minecraftnativeintelligence;

import java.util.Map;
import java.util.Set;

/** Server-derived facts the validator may use; never populate these from a request. */
public record ActionValidationContext(
        String agentId,
        long sessionEpoch,
        long observationSequence,
        long gameTick,
        long maxObservationLag,
        int inventorySize,
        boolean hungry,
        Set<String> supportedCapabilities,
        Set<String> permittedActions,
        Set<String> visibleEntityRefs,
        Set<String> reachableEntityRefs,
        Set<String> visibleBlockRefs,
        Set<String> reachableBlockRefs,
        Set<String> mineableBlockRefs,
        Set<String> availableRecipeIds,
        Set<String> activeRequestIds,
        Set<String> seenRequestIds,
        Set<String> blockedCooldowns,
        Map<Integer, ItemState> inventory,
        Map<String, ItemState> heldItems) {

    public record ItemState(String itemId, int count, boolean edible, boolean placeable, String equipmentSlot) {
        public ItemState {
            if (itemId == null || itemId.isBlank() || count < 0) {
                throw new IllegalArgumentException("item state requires an ID and nonnegative count");
            }
        }
    }

    public ActionValidationContext {
        if (agentId == null || agentId.isBlank() || sessionEpoch < 0 || observationSequence < 0
                || gameTick < 0 || maxObservationLag < 0 || inventorySize < 9) {
            throw new IllegalArgumentException("invalid action validation context");
        }
        supportedCapabilities = Set.copyOf(supportedCapabilities);
        permittedActions = Set.copyOf(permittedActions);
        visibleEntityRefs = Set.copyOf(visibleEntityRefs);
        reachableEntityRefs = Set.copyOf(reachableEntityRefs);
        visibleBlockRefs = Set.copyOf(visibleBlockRefs);
        reachableBlockRefs = Set.copyOf(reachableBlockRefs);
        mineableBlockRefs = Set.copyOf(mineableBlockRefs);
        availableRecipeIds = Set.copyOf(availableRecipeIds);
        activeRequestIds = Set.copyOf(activeRequestIds);
        seenRequestIds = Set.copyOf(seenRequestIds);
        blockedCooldowns = Set.copyOf(blockedCooldowns);
        inventory = Map.copyOf(inventory);
        heldItems = Map.copyOf(heldItems);
    }

    public static String actionCapability(String actionType) {
        return "mni.actions." + actionType + ".v0";
    }
}
