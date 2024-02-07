from typing import Optional, Dict, Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD

from custom_components.aquanet_water_sensor.AquanetApi import AquanetApi

AUTH_SCHEMA = vol.Schema({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Required("meter_id"): cv.string,
})


class AquanetWaterConfigFlow(ConfigFlow, domain="aquanet_water_sensor"):

    async def async_step_import(self, import_config):
        return self.async_abort(reason="one_instance_at_a_time_please")

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        errors: Dict[str, str] = {}
        description_placeholders = {"error_info": ""}
        if user_input is not None:
            api = AquanetApi(user_input[CONF_USERNAME], user_input[CONF_PASSWORD])
            try:
                await self.hass.async_add_executor_job(api.login)
                return self.async_create_entry(title="Aquanet sensor", data=user_input)
            except Exception as e:
                errors = {"login_failed": "verify_connection_failed"}
                description_placeholders = {"error_info": "EBOK Login Failed"}
        return self.async_show_form(
            step_id="user", data_schema=AUTH_SCHEMA, errors=errors, description_placeholders=description_placeholders
        )
