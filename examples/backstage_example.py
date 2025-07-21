#!/usr/bin/env python3
"""
Backstage API Usage Example

This script demonstrates how to use the Backstage API client to interact with
a Backstage instance. It shows various operations like fetching entities,
querying by filters, and handling pagination.

Prerequisites:
1. Set up your .env file with BACKSTAGE_BASE_URL
2. Ensure your Backstage instance is accessible
3. Install dependencies: pip install aiohttp multidict

Usage:
    python tools/backstage_example.py
"""

import asyncio
import logging
from multidict import MultiDict

from wrench.core.api.backstage import create_api

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_query_components():
    """
    Example: Query for specific components using filters.

    This demonstrates how to use the get_entities_by_query method
    to filter entities by kind (Component in this case).
    """
    logger.info('=== Example: Query Components ===')

    api = create_api()

    query_params = MultiDict([('filter', 'kind=component'), ('limit', '10')])

    async with api:
        try:
            components = await api.get_entities_by_query(query_params=query_params)
            logger.info(f'Found {len(components)} components')

            for component in components:
                metadata = component.get('metadata', {})
                spec = component.get('spec', {})

                logger.info(f'Component: {metadata.get("name", "Unknown")}')
                logger.info(
                    f'  Description: {metadata.get("description", "No description")}'
                )
                logger.info(f'  Owner: {spec.get("owner", "Unknown")}')
                logger.info(f'  Type: {spec.get("type", "Unknown")}')
                logger.info(f'  Lifecycle: {spec.get("lifecycle", "Unknown")}')
                logger.info('---')

        except Exception as e:
            logger.error(f'Error querying components: {e}')


async def example_query_apis():
    """
    Example: Query for API entities.

    This shows how to filter for API entities and extract
    relevant information about them.
    """
    logger.info('=== Example: Query APIs ===')

    api = create_api()

    query_params = MultiDict([('filter', 'kind=api'), ('limit', '5')])

    async with api:
        try:
            apis = await api.get_entities_by_query(query_params=query_params)
            logger.info(f'Found {len(apis)} APIs')

            for api_entity in apis:
                metadata = api_entity.get('metadata', {})
                spec = api_entity.get('spec', {})

                logger.info(f'API: {metadata.get("name", "Unknown")}')
                logger.info(
                    f'  Description: {metadata.get("description", "No description")}'
                )
                logger.info(f'  Type: {spec.get("type", "Unknown")}')
                logger.info(f'  Owner: {spec.get("owner", "Unknown")}')
                logger.info('---')

        except Exception as e:
            logger.error(f'Error querying APIs: {e}')


async def example_query_by_owner():
    """
    Example: Query entities by owner.

    This demonstrates filtering entities based on the owner field.
    """
    logger.info('=== Example: Query by Owner ===')

    api = create_api()

    owner_filter = 'spec.owner=dl-platinum'
    query_params = MultiDict([('filter', owner_filter), ('limit', '10')])

    async with api:
        try:
            entities = await api.get_entities_by_query(query_params=query_params)
            logger.info(f'Found {len(entities)} entities owned by dl-platinum')

            # Group by kind
            by_kind = {}
            for entity in entities:
                kind = entity.get('kind', 'Unknown')
                by_kind[kind] = by_kind.get(kind, 0) + 1

            logger.info('Entities by kind:')
            for kind, count in by_kind.items():
                logger.info(f'  {kind}: {count}')

        except Exception as e:
            logger.error(f'Error querying by owner: {e}')


async def example_error_handling():
    """
    Example: Demonstrate error handling.

    Shows how the API client handles various error conditions.
    """
    logger.info('=== Example: Error Handling ===')

    api = create_api()

    async with api:
        # Invalid filter (this might cause an error depending on your Backstage setup)
        try:
            query_params = MultiDict([('filter', 'invalid.filter=nonexistent')])
            entities = await api.get_entities_by_query(query_params=query_params)
            logger.info(
                f'Query with potentially invalid filter returned {len(entities)} entities'
            )
        except Exception as e:
            logger.warning(f'Expected error with invalid filter: {e}')


async def main():
    """
    Main function that runs all examples.
    """
    logger.info('Starting Backstage API Examples')
    logger.info('Make sure your .env file is configured with BACKSTAGE_BASE_URL')

    try:
        await example_query_components()
        await example_query_apis()
        await example_query_by_owner()
        await example_error_handling()

        logger.info('All examples completed successfully!')

    except Exception as e:
        logger.error(f'Error running examples: {e}')
        logger.error(
            'Check your .env configuration and Backstage instance connectivity'
        )


if __name__ == '__main__':
    asyncio.run(main())
