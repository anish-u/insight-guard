import logging
from functools import lru_cache
from neo4j import GraphDatabase, Driver
from .config import settings

logger = logging.getLogger(__name__)

_driver: Driver | None = None


def init_driver() -> None:
  global _driver
  if _driver is None:
    logger.info("Initializing Neo4j driver...")
    _driver = GraphDatabase.driver(
      settings.neo4j_uri,
      auth=(settings.neo4j_user, settings.neo4j_password),
      max_connection_lifetime=60 * 60,
      max_connection_pool_size=50,
      connection_acquisition_timeout=10,
    )


def get_driver() -> Driver:
  global _driver
  if _driver is None:
    init_driver()
  assert _driver is not None
  return _driver


async def close_driver() -> None:
  global _driver
  if _driver is not None:
    logger.info("Closing Neo4j driver...")
    await _driver.close()
    _driver = None


@lru_cache(maxsize=1)
def driver_dependency() -> Driver:
  return get_driver()
