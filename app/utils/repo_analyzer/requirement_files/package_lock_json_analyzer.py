from json import load


async def analyze_package_lock_json(
    requirement_files: dict[str, dict[str, dict | str]],
    repository_path: str,
    requirement_file_name: str,
) -> dict[str, dict[str, dict | str]]:
    file = open(f"{repository_path}/{requirement_file_name}")
    requirement_file_name = requirement_file_name.replace("/master/", "").replace(
        "/main/", ""
    )
    requirement_files[requirement_file_name] = {
        "manager": "NPM",
        "requirement": {},
    }
    try:
        data = load(file)
        requirement = {}
        if "dependencies" in data:
            for package, details in data["dependencies"].items():
                version = details.get("version")
                if version and version.count(".") == 2 and not any(op in version for op in ['<', '>', '=']):
                    requirement[package] = f"== {version}"
                else:
                    requirement[package] = version
        requirement_files[requirement_file_name]["requirement"] = requirement
    except Exception:
        pass
    return requirement_files
