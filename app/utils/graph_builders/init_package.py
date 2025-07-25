from typing import Any

from app.schemas import InitPackageRequest

from .managers import (
    cargo_create_package,
    cargo_search_new_versions,
    maven_create_package,
    maven_search_new_versions,
    npm_create_package,
    npm_search_new_versions,
    nuget_create_package,
    nuget_search_new_versions,
    pypi_create_package,
    pypi_search_new_versions,
    rubygems_create_package,
    rubygems_search_new_versions,
)


async def create_package(init_package_request: InitPackageRequest) -> None:
    match init_package_request.node_type.value:
        case "CargoPackage":
            await cargo_create_package(init_package_request.package_name)
        case "MavenPackage":
            if ":" not in init_package_request.package_name:
                raise ValueError("Maven package name must be in the format 'group_id:artifact_id'")
            group_id, artifact_id = init_package_request.package_name.split(":")
            await maven_create_package(group_id, artifact_id)
        case "NPMPackage":
            await npm_create_package(init_package_request.package_name)
        case "NuGetPackage":
            await nuget_create_package(init_package_request.package_name)
        case "PyPIPackage":
            await pypi_create_package(init_package_request.package_name)
        case "RubyGemsPackage":
            await rubygems_create_package(init_package_request.package_name)
        case _:
            raise ValueError(f"Unsupported node type: {init_package_request.node_type.value}")


async def search_new_versions(package: dict[str, Any], node_type: str) -> None:
    match node_type:
        case "CargoPackage":
            await cargo_search_new_versions(package)
        case "MavenPackage":
            await maven_search_new_versions(package)
        case "NPMPackage":
            await npm_search_new_versions(package)
        case "NuGetPackage":
            await nuget_search_new_versions(package)
        case "PyPIPackage":
            await pypi_search_new_versions(package)
        case "RubyGemsPackage":
            await rubygems_search_new_versions(package)
        case _:
            raise ValueError(f"Unsupported node type: {node_type}")
