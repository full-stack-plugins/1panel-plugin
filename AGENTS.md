# Plugin maintenance

- Skill content is maintained only in source repositories listed in skills.lock.json. No local skill exceptions.
- Change and release the source first, then update the source ref and run scripts/vendor/skill_vendor.py update. Never patch only the snapshot.
- Keep complete resources and licenses. Run check_snapshot.py offline and skill_vendor.py check against upstream before release.
- Every published change bumps the version. Keep root/native manifests, repository marketplace and the aggregate full-stack-plugins catalog synchronized; installation sources and logos use the corresponding immutable tag.
- Publish plugin tags and GitHub Releases before aggregate marketplace entries. Preserve user changes and existing release tags.
- Do not modify installed caches, install dependencies, expose credentials or run real panel operations as packaging verification.
