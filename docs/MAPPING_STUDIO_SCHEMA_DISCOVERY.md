# Mapping Studio — Schema Discovery and Drift

The simulator schema-discovery endpoint compares baseline and discovered fields. It reports new, removed, type, required/nullable, and enum changes, assigns risk, and never auto-maps or activates a change. Configured connectors can call their provider health and schema endpoints through the credential reference held in server configuration; credentials are never returned in responses or audit details.

Real provider health/schema evidence remains an operational gate until an approved endpoint and credential are supplied.
