# civilite

Library for managing outdoor lighting when building occupancy and available daylight must be considered.

## Overview

When a building is occupied on a given schedule for an event, outdoor lighting for the building and premises must also take the available daylight into account.  This library aims to allow easy integration of this logic into an automation system.

## Requirements

1. An occupancy event is defined by a start time and an end time.  This shall include time before the actual occupancy of the building to allow for outdoor activities directly before and after the event (parking, etc.)
1. If sunset occurs during an event, lights shall turn on at sunset and turn off at end of event.
1. If multiple events are scheduled, any gaps between events less than 30 minutes shall be considered as if the building is occupied.
1. Occupancy schedule shall be loaded from an external source, preferably via a known API.

## External Dependencies

* [astral](https://pypi.org/project/astral/) - for calculation of location-based sunset/sunrise
* [reportlab](https://pypi.org/project/reportlab/) - for generation of PDF documents
