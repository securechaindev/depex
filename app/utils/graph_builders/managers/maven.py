from datetime import datetime, timedelta
from typing import Any

from app.apis import get_maven_requirement, get_maven_versions
from app.services import (
    count_number_of_versions_by_package,
    create_package_and_versions,
    create_requirement_file,
    create_versions,
    read_package_by_name,
    read_versions_names_by_package,
    relate_packages,
    update_package_moment,
)
from app.utils.others import version_to_serial_number

from .vulnerabilities import attribute_vulnerabilities


async def maven_create_requirement_file(requirement_file_name: str, file: Any, repository_id: str) -> None:
    new_req_file_id = await create_requirement_file(
        {"name": requirement_file_name, "manager": file["manager"], "moment": datetime.now()}, repository_id
    )
    await maven_generate_packages(file["requirement"], new_req_file_id)


async def maven_generate_packages(
    requirement: dict[str, str],
    parent_id: str,
    parent_version_name: str | None = None
) -> None:
    known_packages = []
    for package_name, constraints in requirement.items():
        group_id, artifact_id = package_name.split(":")
        package = await read_package_by_name("MavenPackage", f"{group_id}:{artifact_id}")
        if package:
            package["parent_id"] = parent_id
            package["parent_version_name"] = parent_version_name
            package["constraints"] = constraints
            if package["moment"] < datetime.now() - timedelta(days=10):
                await maven_search_new_versions(package)
            known_packages.append(package)
        else:
            await maven_create_package(group_id, artifact_id, constraints, parent_id, parent_version_name)
    await relate_packages("MavenPackage", known_packages)


async def maven_create_package(
    group_id: str,
    artifact_id: str,
    constraints: str | None = None,
    parent_id: str | None = None,
    parent_version_name: str | None = None,
) -> None:
    versions = await get_maven_versions(group_id, artifact_id)
    if versions:
        attributed_versions = [
            await attribute_vulnerabilities(f"{group_id}:{artifact_id}", version)
            for version in versions
        ]
        created_versions = await create_package_and_versions(
            "MavenPackage",
            {"group_id": group_id, "artifact_id": artifact_id, "name": f"{group_id}:{artifact_id}", "vendor": "n/a", "moment": datetime.now()},
            attributed_versions,
            constraints,
            parent_id,
            parent_version_name,
        )
        for created_version in created_versions:
            await maven_extract_packages(group_id, artifact_id, created_version)


async def maven_extract_packages(
    parent_group_id: str,
    parent_artifact_id: str,
    version: dict[str, Any]
) -> None:
    requirement = await get_maven_requirement(
        parent_group_id,
        parent_artifact_id,
        version["name"],
    )
    await maven_generate_packages(requirement, version["id"], f"{parent_group_id}:{parent_artifact_id}")


async def maven_search_new_versions(package: dict[str, Any]) -> None:
    versions = await get_maven_versions(package["group_id"], package["artifact_id"])
    count = await count_number_of_versions_by_package("MavenPackage", package["name"])
    if count < len(versions):
        attributed_versions: list[dict[str, Any]] = []
        actual_versions = await read_versions_names_by_package("MavenPackage", package["name"])
        for version in versions:
            if version["name"] not in actual_versions:
                version["serial_number"] = await version_to_serial_number(version["name"])
                attributed_versions.append(
                    await attribute_vulnerabilities(package["name"], version)
                )
        created_versions = await create_versions(
            "MavenPackage",
            package["name"],
            attributed_versions,
        )
        for version in created_versions:
            await maven_extract_packages(package["group_id"], package["artifact_id"], version)
    await update_package_moment("MavenPackage", package["name"])
