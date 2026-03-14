# Alerts API
Author: Dan Reed
For: Censys

## Use
This is an api for retrieving alerts from the system.  This api handles the communication to upstream third party security technology providers, reffered to as "SecTech" or "Providers" from here forward.

This API requires some environment configuration, you can do so by adding a `.env` file to the project root.

## Folder Structure
- The api functionality is maintained in the `api` subfolder.
- Then a version folder `v1`
- The `models` provide a data model
- the `providers` provide endpoints for `/alerts` and simulate 3rd part security technology responses for enrichment.
