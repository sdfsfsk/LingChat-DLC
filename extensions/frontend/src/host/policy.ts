import type { ScriptInfo } from "@lingchat/host/stores/modules/game/state";
export const storyPolicy = (script: ScriptInfo | null) => ({
  lockPet: script?.contentWarning === "horror",
  returnToMenu: script?.contentWarning === "horror",
});
