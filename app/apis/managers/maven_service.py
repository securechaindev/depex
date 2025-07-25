from asyncio import TimeoutError, sleep
from typing import Any
from xml.etree.ElementTree import ParseError, fromstring

from aiohttp import ClientConnectorError, ContentTypeError

from app.cache import get_cache, set_cache
from app.http_session import get_session
from app.logger import logger
from app.utils.others import version_to_serial_number


async def get_maven_versions(group_id: str, artifact_id: str) -> list[dict[str, Any]]:
    key = f"{group_id}:{artifact_id}"
    response = await get_cache(key)
    if response:
        versions = response
    else:
        versions: list[dict[str, Any]] = []
        session = await get_session()
        start = 0
        while True:
            url = f"https://search.maven.org/solrsearch/select?q=g:{group_id}+AND+a:{artifact_id}&core=gav&rows=200&start={start}"
            while True:
                try:
                    logger.info(f"Maven - {url}")
                    async with session.get(url) as response:
                        response = await response.json()
                        await set_cache(url, response)
                        break
                except (ClientConnectorError, TimeoutError):
                    await sleep(5)
                except ContentTypeError:
                    return versions
            start += 200
            if not response.get("response").get("docs", []):
                break
            for version in response.get("response", {}).get("docs", []):
                name = version.get("v")
                versions.append({"name": name, "serial_number": await version_to_serial_number(name)})
        await set_cache(key, versions)
    return versions


async def get_maven_version(group_id: str, artifact_id: str, version_name: str) -> dict[str, Any]:
    key = f"version:{group_id}:{artifact_id}:{version_name}"
    response = await get_cache(key)
    if response:
        version = response
    else:
        versions: list[dict[str, Any]] = []
        session = await get_session()
        start = 0
        while True:
            url = f"https://search.maven.org/solrsearch/select?q=g:{group_id}+AND+a:{artifact_id}&core=gav&rows=200&start={start}"
            while True:
                try:
                    logger.info(f"Maven - {url}")
                    async with session.get(url) as response:
                        response = await response.json()
                        await set_cache(url, response)
                        break
                except (ClientConnectorError, TimeoutError):
                    await sleep(5)
                except ContentTypeError:
                    return versions
            start += 200
            if not response.get("response").get("docs", []):
                break
            versions.extend([version.get("v") for version in response.get("response", {}).get("docs", [])])
        if version_name in versions:
            version = {"name": version_name, "serial_number": await version_to_serial_number(version_name)}
            await set_cache(key, version)
        else:
            raise ValueError(f"Version {version_name} not found for package {group_id}:{artifact_id}")
    return version


async def get_maven_requirement(group_id: str, artifact_id: str, version_name: str) -> dict[str, list[str] | str]:
    key = f"requirement :{group_id}:{artifact_id}:{version_name}"
    response = await get_cache(key)
    if response:
        require_packages = response
    else:
        require_packages: dict[str, Any] = {}
        session = await get_session()
        url = f"https://repo1.maven.org/maven2/{group_id.replace('.', '/')}/{artifact_id}/{version_name}/{artifact_id}-{version_name}.pom"
        while True:
            try:
                logger.info(f"Maven - {url}")
                async with session.get(url) as response:
                    response = await response.text()
                    break
            except (ClientConnectorError, TimeoutError):
                await sleep(5)
        try:
            root = fromstring(response)
            namespace = {"mvn": "http://maven.apache.org/POM/4.0.0"}
            for dep in root.findall(".//mvn:dependency", namespace):
                dep_group_id = dep.find("mvn:groupId", namespace).text
                dep_artifact_id = dep.find("mvn:artifactId", namespace).text
                dep_version = dep.find("mvn:version", namespace)
                dep_version_text = dep_version.text if dep_version is not None else "latest"
                if not any(
                    char in dep_version_text for char in ["[", "]", "(", ")"]
                ):
                    dep_version_text = "[" + dep_version_text + "]"
                require_packages[
                    (dep_group_id, dep_artifact_id)
                ] = dep_version_text
        except ParseError:
            pass
        await set_cache(key, require_packages)
    return require_packages
