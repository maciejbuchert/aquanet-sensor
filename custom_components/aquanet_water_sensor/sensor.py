"""Platform for sensor integration."""
from __future__ import annotations

import logging
import string
from datetime import timedelta
from typing import Callable, Optional
import json

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import SensorEntity, PLATFORM_SCHEMA, SensorStateClass, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType, HomeAssistantType

from .AquanetApi import AquanetApi

_LOGGER = logging.getLogger(__name__)
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Required("meter_id"): cv.string,
})
SCAN_INTERVAL = timedelta(hours=8)


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities,
):
    user = config_entry.data[CONF_USERNAME]
    password = config_entry.data[CONF_PASSWORD]
    api = AquanetApi(user, password)
    async_add_entities([AquanetSensor(hass, api, config_entry.data["meter_id"])], update_before_add=True)


async def async_setup_platform(
        hass: HomeAssistantType,
        config: ConfigType,
        async_add_entities: Callable,
        discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    api = AquanetApi(config.get(CONF_USERNAME), config.get(CONF_PASSWORD))
    async_add_entities([AquanetSensor(hass, api, config.get("meter_id"))], update_before_add=True)


class AquanetSensor(SensorEntity):
    def __init__(self, hass, api: AquanetApi, meter_id: string) -> None:
        self._attr_native_unit_of_measurement = UnitOfVolume.CUBIC_METERS
        self._state = None
        self._attr_device_class = SensorDeviceClass.GAS
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self.hass = hass
        self.api = api
        self.meter_id = meter_id
        self.entity_name = "Aquanet Water Sensor " + meter_id

    @property
    def unique_id(self) -> str | None:
        return "aquanet_sensor" + self.meter_id

    @property
    def device_info(self):
        return {
            "identifiers": {("aquanet_water_sensor", self.meter_id)},
            "name": f"AQUANET WATER METER ID {self.meter_id}",
            "manufacturer": "AQUANET",
            "model": self.meter_id,
            "via_device": None,
        }

    @property
    def name(self) -> str:
        _LOGGER.debug(f"{self.unique_id} - call.name: {self.entity_name}")
        return self.entity_name

    @property
    def extra_state_attributes(self):
        attrs = dict()
        if self._state is not None:
            attrs["wear"] = self._state
            attrs["wear_unit_of_measurment"] = UnitOfVolume.CUBIC_METERS

        _LOGGER.debug(f"{self.unique_id} - call.extra_state_attributes: {json.dumps(attrs)}")
        return attrs

    @property
    def state(self):
        _LOGGER.debug(f"{self.unique_id} - call.state: {self._state}")
        if self._state is None:
            return None
        return self._state

    async def async_update(self):
        _LOGGER.debug(f"{self.unique_id} - call.async_update: {self.latestMeterReading}")
        latest_meter_reading = await self.hass.async_add_executor_job(self.latestMeterReading)
        self._state = latest_meter_reading

    def latestMeterReading(self):
        return self.api.consumptionChart(self.meter_id)