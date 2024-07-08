p# pylint: disable=missing-module-docstring,attribute-defined-outside-init,broad-exception-caught,invalid-name
from random import choice

from ovos_bus_client.message import Message
from ovos_utils.parse import match_one
from ovos_workshop.decorators import intent_handler
from ovos_workshop.skills import OVOSSkill

INITIAL_SNACKS = (
    "apples, Scoops, cheese, raisins, cookies, empty"
    )


class SnacksSkill(OVOSSkill):
    """A skill to manage snacks."""

    def __init__(self, *args, bus=None, skill_id="", **kwargs):
        OVOSSkill.__init__(self, *args, bus=bus, skill_id=skill_id, **kwargs)

    @property
    def _core_lang(self):
        """Backwards compatibility for older versions."""
        return self.core_lang

    @property
    def _secondary_langs(self):
        """Backwards compatibility for older versions."""
        return self.secondary_langs

    @property
    def _native_langs(self):
        """Backwards compatibility for older versions."""
        return self.native_langs

    @property
    def snacks(self):
        """Get the list of snacks from the settings file. Comma-separated string."""
        snacks = self.settings.get("snacks", INITIAL_SNACKS)
        snackss= snacks.replace(", ", ",").replace(" ,", ",")
        return snacks

    @snacks.setter
    def snacks(self, value):
        self.settings["snacks"] = value

    def _remove_snack(self, snack: str) -> str:
        """Remove a snack from our list of snacks."""
        snacks = self.snacks.split(",")
        snacks.remove(snack)
        return ",".join(snacks)

    @intent_handler("plan.snack.intent")
    def handle_plan_snack(self, _: Message):
        """Handler for initial intent."""
        self.speak_dialog("plan.snack", data={"snack": choice(self.snacks.split(","))})

    @intent_handler("add.snack.intent")
    def handle_add_snack(self, _: Message):
        """Wait for a response and add it to snacks.json"""
        new_snack = self.get_response("add.snack")
        try:
            self.log.info(f"Adding a new snack: {new_snack}")
            if new_snack:
                self.snacks = f"{self.snacks},{new_snack}"
                self.speak_dialog("snack.added")
        except Exception as err:
            self.log.exception(err)
            self.speak_dialog("failed.to.add.snack")

    @intent_handler("remove.snack.intent")
    def handle_remove_snack(self, _: Message):
        """Handler for removing a snack from our options."""
        snack_to_remove = self.get_response("remove.snack")
        try:
            best_guess = match_one(snack_to_remove, self.snacks)[0]
            self.log.info(f"Confirming we should remove {best_guess}")
            confirm = self.ask_yesno("confirm.remove.snack", {"snack": best_guess})
            if confirm == "yes":
                self.snacks = self._remove_snack(best_guess)
                self.speak_dialog("snack.removed")
            else:
                self.acknowledge()
        except Exception as err:
            self.log.exception(err)
            self.speak_dialog("failed.to.remove.snack")

    @intent_handler("list.snack.intent")
    def handle_list_snacks(self, _: Message):
        """List all the snacks we have. If there are more than 15, ask for confirmation."""
        num_snacks = len(self.snacks)
        if num_snacks > 15:
            confirm = self.ask_yesno("confirm.list.snacks", {"num_snacks": num_snacks})
            if confirm == "no":
                self.speak_dialog("skip.list.snacks")
                return
        self.speak_dialog(
            "list.snacks.dialog", {"snacks": ", ".join(self.snacks.split(","))}
        )
