"""Entity data management for Software Catalog export."""

import json
import typing as tp

from multidict import MultiDict

from wrench.misc import transform
from wrench.core.api import backstage


class Entity:
    """Manages entity data from Software Catalog for export operations."""

    def __init__(self):
        self._data: tp.Any = None
        self.api: backstage.API = backstage.create_api()

    @property
    def data(self) -> tp.Any:
        return self._data

    async def ingest(self, query_params: MultiDict) -> None:
        """Ingest data from Software Catalog (Backstage).

        :param filter: Query that is sent to Software Catalog.
        :param transform: JQ program (the simplest is '.')
        """
        async with self.api:
            entities = await self.api.get_entities_by_query(query_params=query_params)
        self._data = entities

    def clean_description_field(self) -> None:
        """Clean description fields by removing trailing newlines."""
        if not self._data:
            return

        for row in self._data:
            if not isinstance(row, dict):
                continue

            metadata = row.get('metadata')
            if metadata and isinstance(metadata, dict):
                description = metadata.get('description')
                if description and isinstance(description, str):
                    metadata['description'] = description.strip('\n')

    def export_csv(self, filename: str | None = None) -> None:
        """Export entity data to CSV format."""
        import io

        import polars  # type: ignore[import-untyped]

        data = transform.transform(self._data, transform.JQ_FLATTEN)
        entities_json = json.dumps(data)
        if filename:
            df = polars.read_json(io.StringIO(entities_json))
            df.write_csv(filename)
        else:
            print(entities_json)

    def export_json(self, filename: str | None = None) -> None:
        """Export entity data to JSON format."""
        entities_json = json.dumps(self._data)
        if filename:
            with open(file=filename, mode='w') as f:
                f.write(entities_json)
        else:
            print(entities_json)

    def export_txt(self, filename: str | None = None) -> None:
        """Export entity data to plain text format."""
        if filename:
            with open(file=filename, mode='w') as f:
                print(self._data, file=f)
        else:
            print(self._data)
