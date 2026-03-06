import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.edges_repo import EdgesRepository
from app.repositories.nodes_repo import NodesRepository


class PathService:
    """Shortest-path use-case (keeps business logic separate from transport)."""

    def __init__(self, db: AsyncSession):
        self._db = db
        self._nodes = NodesRepository(db)
        self._edges = EdgesRepository(db)

    async def find_shortest_path_bfs(
        self,
        start_title: str,
        end_title: str,
        on_level_done=None,
        on_node_explored=None,
        max_levels: int = 20,
    ) -> list[str]:
        start = await self._nodes.get_by_title(start_title)
        end = await self._nodes.get_by_title(end_title)
        if not start or not end:
            raise ValueError("start or end node not found")

        if start.id == end.id:
            return [start.title]

        visited: set[uuid.UUID] = {start.id}
        parent: dict[uuid.UUID, uuid.UUID] = {}

        frontier: list[uuid.UUID] = [start.id]
        level = 1

        while frontier and level <= max_levels:
            pairs = await self._edges.get_neighbors(frontier)
            next_frontier: list[uuid.UUID] = []
            batch_nodes: list[uuid.UUID] = []

            for src_id, dst_id in pairs:
                if dst_id in visited:
                    continue
                visited.add(dst_id)
                parent[dst_id] = src_id
                next_frontier.append(dst_id)
                batch_nodes.append(dst_id)

                if on_node_explored:
                    on_node_explored(level, dst_id)

                if dst_id == end.id:
                    if on_level_done and batch_nodes:
                        on_level_done(level, batch_nodes)
                    return await self._reconstruct_path_titles(parent, start.id, end.id)

            if on_level_done and batch_nodes:
                on_level_done(level, batch_nodes)

            frontier = next_frontier
            level += 1

        raise ValueError("no path found (or max_levels exceeded)")

    async def _reconstruct_path_titles(
        self, parent: dict[uuid.UUID, uuid.UUID], start_id: uuid.UUID, end_id: uuid.UUID
    ) -> list[str]:
        path_ids: list[uuid.UUID] = []
        at = end_id
        while True:
            path_ids.append(at)
            if at == start_id:
                break
            if at not in parent:
                raise ValueError("no path found")
            at = parent[at]
        path_ids.reverse()

        nodes = await self._nodes.get_by_ids(path_ids)
        by_id = {n.id: n for n in nodes}
        return [by_id[i].title for i in path_ids]

