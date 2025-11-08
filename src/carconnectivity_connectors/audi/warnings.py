"""
Module for vehicle health warnings for Audi vehicles.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from carconnectivity.attributes import BooleanAttribute, EnumAttribute, GenericAttribute, StringAttribute
from carconnectivity.objects import GenericObject

if TYPE_CHECKING:
    from carconnectivity_connectors.audi.vehicle import AudiVehicle


class AudiWarnings(GenericObject):
    """
    AudiWarnings class for handling Audi vehicle health warnings.

    This class provides access to vehicle health warnings including
    priority levels, categories, and detailed warning information.
    """

    def __init__(self, vehicle: AudiVehicle | None = None) -> None:
        super().__init__(object_id="warnings", parent=vehicle)

        # Service availability flags
        self.service_available: BooleanAttribute = BooleanAttribute(
            "service_available", parent=self, tags={"connector_custom"}
        )
        self.has_active_license: BooleanAttribute = BooleanAttribute(
            "has_active_license", parent=self, tags={"connector_custom"}
        )
        self.wake_up_warnings_supported: BooleanAttribute = BooleanAttribute(
            "wake_up_warnings_supported", parent=self, tags={"connector_custom"}
        )

        # Warning counts by priority
        self.critical_count: GenericAttribute = GenericAttribute("critical_count", parent=self, tags={"connector_custom"})
        self.high_count: GenericAttribute = GenericAttribute("high_count", parent=self, tags={"connector_custom"})
        self.medium_count: GenericAttribute = GenericAttribute("medium_count", parent=self, tags={"connector_custom"})
        self.low_count: GenericAttribute = GenericAttribute("low_count", parent=self, tags={"connector_custom"})

        # Storage for individual warnings (as generic attributes)
        self._warnings_list: List[GenericObject] = []

    def update_warnings(self, warnings_data: List[Dict[str, Any]], captured_at: datetime) -> None:
        """
        Update warnings from API data.

        Args:
            warnings_data: List of warning dictionaries from the API
            captured_at: Timestamp when the data was captured
        """
        # Clear existing warnings
        for warning in self._warnings_list:
            if hasattr(self, warning.object_id):
                delattr(self, warning.object_id)
        self._warnings_list = []

        # Count warnings by priority
        priority_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

        # Create individual warning objects
        for idx, warning_data in enumerate(warnings_data, start=1):
            warning_id = f"warning_{idx}"
            warning_obj = AudiWarnings.Warning(parent=self, warning_id=warning_id)

            # Set warning attributes from data
            if "id" in warning_data:
                warning_obj.warning_id._set_value(warning_data["id"], measured=captured_at)
            if "priority" in warning_data:
                priority = warning_data["priority"]
                if priority in [item.value for item in AudiWarnings.WarningPriority]:
                    warning_obj.priority._set_value(AudiWarnings.WarningPriority(priority), measured=captured_at)
                    # Count by priority
                    if priority in priority_counts:
                        priority_counts[priority] += 1
            if "category" in warning_data:
                warning_obj.category._set_value(warning_data["category"], measured=captured_at)
            if "description" in warning_data:
                warning_obj.description._set_value(warning_data["description"], measured=captured_at)
            if "acknowledged" in warning_data:
                warning_obj.acknowledged._set_value(warning_data["acknowledged"], measured=captured_at)

            # Add to vehicle
            setattr(self, warning_id, warning_obj)
            self._warnings_list.append(warning_obj)

        # Update priority counts
        self.critical_count._set_value(priority_counts["CRITICAL"], measured=captured_at)
        self.high_count._set_value(priority_counts["HIGH"], measured=captured_at)
        self.medium_count._set_value(priority_counts["MEDIUM"], measured=captured_at)
        self.low_count._set_value(priority_counts["LOW"], measured=captured_at)

    class Warning(GenericObject):
        """
        Represents an individual vehicle health warning.
        """

        def __init__(self, parent: Optional[GenericObject] = None, warning_id: str = "warning") -> None:
            super().__init__(object_id=warning_id, parent=parent)

            self.warning_id: StringAttribute = StringAttribute("id", parent=self, tags={"connector_custom"})
            self.priority: EnumAttribute = EnumAttribute("priority", parent=self, tags={"connector_custom"})
            self.category: StringAttribute = StringAttribute("category", parent=self, tags={"connector_custom"})
            self.description: StringAttribute = StringAttribute("description", parent=self, tags={"connector_custom"})
            self.acknowledged: BooleanAttribute = BooleanAttribute("acknowledged", parent=self, tags={"connector_custom"})

    class WarningPriority(Enum):
        """
        Enum representing warning priority levels.
        """

        CRITICAL = "CRITICAL"
        HIGH = "HIGH"
        MEDIUM = "MEDIUM"
        LOW = "LOW"
        UNKNOWN = "UNKNOWN"
