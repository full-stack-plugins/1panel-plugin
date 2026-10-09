# Plugin maintenance

- Skill content is maintained only in source repositories listed in skills.lock.json. No local skill exceptions.
- Change and release the source first, then update the source ref and run scripts/vendor/skill_vendor.py update. Never patch only the snapshot.
- Keep complete resources and licenses. Run check_snapshot.py offline and skill_vendor.py check against upstream before release.
- Every published change bumps the version. Keep root/native manifests, repository marketplace and the aggregate full-stack-plugins catalog synchronized; installation sources and logos use the corresponding immutable tag.
- Publish plugin tags and GitHub Releases before aggregate marketplace entries. Preserve user changes and existing release tags.
- Do not modify installed caches, install dependencies, expose credentials or run real panel operations as packaging verification.

<!-- partme-agent-plugin-policy:v1 -->
## Partme Agent Plugin Architecture Rules v1

- 组织级架构规范（跨 `full-aigc-plugins` 与 `full-stack-plugins` 的唯一事实源）：[Partme Agent Plugin Architecture Rules v1](https://github.com/full-aigc-plugins/.github/blob/main/docs/standards/partme-agent-plugin-architecture-rules-v1.md)。
- **Harness 可选**：默认直接使用 Skills + CLI/MCP；只有确有必要时才使用最多一个可发现的 `skills/*-harness/SKILL.md`，其中的 `scripts/harness.py` 同样可选。
- 不重复开发宿主 Agent Runtime、原生 CLI/MCP 业务执行器、持久数据库或权威任务状态。正式功能必须具备可核验的 Agent → Skill/Command → Tool → Artifact 调用链。
- 保留本仓库现有 OpenSpec、技能来源锁、安全门禁、版本发布及 CI 要求；静态检查不能替代真实宿主验收。
- CI 复用组织级 [Partme Plugin Architecture 检查器](https://github.com/full-aigc-plugins/.github/blob/main/scripts/check_plugin_architecture.py)，不得复制独立实现。
<!-- /partme-agent-plugin-policy:v1 -->
