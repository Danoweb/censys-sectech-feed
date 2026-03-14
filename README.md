# censys-sectech-feed
An example for how a feed could pull from sectech, translate the data, and store the data in a standard schema for data-lake or other purposes.

## Three Project Approach
- The `alerts_api` folder contains the mock alerts from various security technology, 
- The `alerts_db` folder contains the database for the security technology alerts, as well as the database for translated, enriched, alert storage from the service.
- The `sectech_api` folder contains a service that looks up events/alerts from security technology it then translates them, enriches them, and stores that data in the db and/or returns that data to the end user.