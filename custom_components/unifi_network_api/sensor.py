"""Sensor platform for UniFi Network API."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfDataRate, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_SITE_NAME, DOMAIN
from .coordinator import UnifiNetworkApiCoordinator


@dataclass(frozen=True, kw_only=True)
class UnifiDeviceSensorDescription(SensorEntityDescription):
    """Describe a UniFi device sensor."""

    value_fn: Callable[[dict[str, Any]], Any]
    source: str = "statistics"  # "info", "details", or "statistics"


DEVICE_SENSORS: tuple[UnifiDeviceSensorDescription, ...] = (
    UnifiDeviceSensorDescription(
        key="state",
        translation_key="device_state",
        icon="mdi:server-network",
        value_fn=lambda d: d.get("info", {}).get("state"),
        source="info",
    ),
    UnifiDeviceSensorDescription(
        key="cpu_utilization",
        translation_key="cpu_utilization",
        icon="mdi:cpu-64-bit",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda d: d.get("statistics", {}).get("cpuUtilizationPct"),
        source="statistics",
    ),
    UnifiDeviceSensorDescription(
        key="memory_utilization",
        translation_key="memory_utilization",
        icon="mdi:memory",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda d: d.get("statistics", {}).get("memoryUtilizationPct"),
        source="statistics",
    ),
    UnifiDeviceSensorDescription(
        key="uptime",
        translation_key="uptime",
        icon="mdi:clock-outline",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: d.get("statistics", {}).get("uptimeSec"),
        source="statistics",
    ),
    UnifiDeviceSensorDescription(
        key="load_average_1min",
        translation_key="load_average_1min",
        icon="mdi:gauge",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda d: d.get("statistics", {}).get("loadAverage1Min"),
        source="statistics",
    ),
    UnifiDeviceSensorDescription(
        key="load_average_5min",
        translation_key="load_average_5min",
        icon="mdi:gauge",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda d: d.get("statistics", {}).get("loadAverage5Min"),
        source="statistics",
    ),
    UnifiDeviceSensorDescription(
        key="load_average_15min",
        translation_key="load_average_15min",
        icon="mdi:gauge",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda d: d.get("statistics", {}).get("loadAverage15Min"),
        source="statistics",
    ),
    UnifiDeviceSensorDescription(
        key="firmware_version",
        translation_key="firmware_version",
        icon="mdi:package-up",
        value_fn=lambda d: d.get("info", {}).get("firmwareVersion"),
        source="info",
    ),
    UnifiDeviceSensorDescription(
        key="firmware_updatable",
        translation_key="firmware_updatable",
        icon="mdi:update",
        value_fn=lambda d: d.get("info", {}).get("firmwareUpdatable"),
        source="info",
    ),
    UnifiDeviceSensorDescription(
        key="uplink_tx_rate",
        translation_key="uplink_tx_rate",
        icon="mdi:upload",
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("statistics", {}).get("uplink", {}).get("txRateBps")
        if d.get("statistics", {}).get("uplink")
        else None,
        source="statistics",
    ),
    UnifiDeviceSensorDescription(
        key="uplink_rx_rate",
        translation_key="uplink_rx_rate",
        icon="mdi:download",
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("statistics", {}).get("uplink", {}).get("rxRateBps")
        if d.get("statistics", {}).get("uplink")
        else None,
        source="statistics",
    ),
    UnifiDeviceSensorDescription(
        key="last_heartbeat",
        translation_key="last_heartbeat",
        icon="mdi:heart-pulse",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: _parse_timestamp(
            d.get("info", {}).get("lastHeartbeatAt")
        ),
        source="info",
    ),
)


def _parse_timestamp(value: str | None) -> datetime | None:
    """Parse an ISO timestamp string to a datetime object."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


@dataclass(frozen=True, kw_only=True)
class UnifiSiteSensorDescription(SensorEntityDescription):
    """Describe a UniFi site-level sensor."""

    value_fn: Callable[[dict[str, Any]], Any]


SITE_SENSORS: tuple[UnifiSiteSensorDescription, ...] = (
    UnifiSiteSensorDescription(
        key="total_clients",
        translation_key="total_clients",
        icon="mdi:account-multiple",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("client_count"),
    ),
    UnifiSiteSensorDescription(
        key="wired_clients",
        translation_key="wired_clients",
        icon="mdi:ethernet",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("client_count_wired"),
    ),
    UnifiSiteSensorDescription(
        key="wireless_clients",
        translation_key="wireless_clients",
        icon="mdi:wifi",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("client_count_wireless"),
    ),
    UnifiSiteSensorDescription(
        key="vpn_clients",
        translation_key="vpn_clients",
        icon="mdi:vpn",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("client_count_vpn"),
    ),
    UnifiSiteSensorDescription(
        key="device_count",
        translation_key="device_count",
        icon="mdi:server-network",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: len(d.get("devices", {})),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up UniFi sensors from a config entry."""
    coordinator: UnifiNetworkApiCoordinator = hass.data[DOMAIN][entry.entry_id]

    tracked_devices: set[str] = set()

    @callback
    def _async_add_new_devices() -> None:
        """Add sensors for newly discovered devices and remove stale ones."""
        new_entities: list[SensorEntity] = []
        current_devices = set(coordinator.data.get("devices", {}).keys())
        new_device_ids = current_devices - tracked_devices

        for device_id in new_device_ids:
            tracked_devices.add(device_id)
            for description in DEVICE_SENSORS:
                new_entities.append(
                    UnifiDeviceSensor(coordinator, entry, device_id, description)
                )

        if new_entities:
            async_add_entities(new_entities)

    # Add site-level sensors (always present)
    site_entities: list[SensorEntity] = [
        UnifiSiteSensor(coordinator, entry, description)
        for description in SITE_SENSORS
    ]
    async_add_entities(site_entities)

    # Add device sensors for initially discovered devices
    _async_add_new_devices()

    # Register listener to add sensors for future device discoveries
    entry.async_on_unload(
        coordinator.async_add_listener(_async_add_new_devices)
    )


class UnifiDeviceSensor(
    CoordinatorEntity[UnifiNetworkApiCoordinator], SensorEntity
):
    """Sensor entity for a UniFi device metric."""

    entity_description: UnifiDeviceSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: UnifiNetworkApiCoordinator,
        entry: ConfigEntry,
        device_id: str,
        description: UnifiDeviceSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._device_id = device_id
        self._attr_unique_id = f"{entry.entry_id}_{device_id}_{description.key}"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available
            and self._device_id in self.coordinator.data.get("devices", {})
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        device_data = (
            self.coordinator.data.get("devices", {})
            .get(self._device_id, {})
            .get("info", {})
        )
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device_data.get("name") or device_data.get("macAddress", self._device_id),
            manufacturer="Ubiquiti",
            model=device_data.get("model"),
            sw_version=device_data.get("firmwareVersion"),
            via_device=(DOMAIN, self.coordinator.config_entry.entry_id),
        )

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        device_data = (
            self.coordinator.data.get("devices", {}).get(self._device_id, {})
        )
        return self.entity_description.value_fn(device_data)


class UnifiSiteSensor(
    CoordinatorEntity[UnifiNetworkApiCoordinator], SensorEntity
):
    """Sensor entity for site-level UniFi metrics."""

    entity_description: UnifiSiteSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: UnifiNetworkApiCoordinator,
        entry: ConfigEntry,
        description: UnifiSiteSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for the controller device."""
        site_name = self._entry.data.get(CONF_SITE_NAME, "UniFi")
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=f"UniFi Controller ({site_name})",
            manufacturer="Ubiquiti",
            model="UniFi Network Controller",
        )

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.coordinator.data)
