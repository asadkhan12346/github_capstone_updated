"""Structural checks for the phase manifest and Copilot configuration."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PHASES = [
    "requirements", "architecture", "design-review", "planning",
    "implementation", "review", "verify", "pr",
]


def allowed_files(agent_text: str) -> list[str]:
    match = re.search(r"(?ms)^## Allowed files\s*$(.*?)(?=^## |\Z)", agent_text)
    return re.findall(r"`([^`]+)`", match.group(1)) if match else []


def frontmatter(text: str) -> str:
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if match is None:
        raise AssertionError("missing YAML frontmatter")
    return match.group(1)


class ConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((ROOT / "sdlc" / "phases.json").read_text(encoding="utf-8"))
        cls.phases = sorted(cls.manifest["phases"], key=lambda phase: phase["order"])

    def test_eight_phase_agent_prompt_and_contract_files_exist(self) -> None:
        self.assertEqual([phase["id"] for phase in self.phases], EXPECTED_PHASES)
        self.assertTrue((ROOT / "docs" / "CONTRACT.md").is_file())
        for phase in self.phases:
            with self.subTest(phase=phase["id"]):
                self.assertTrue((ROOT / phase["agent"]).is_file())
                self.assertTrue((ROOT / phase["prompt"]).is_file())
                self.assertIn(phase["id"], (ROOT / "docs" / "CONTRACT.md").read_text(encoding="utf-8"))

    def test_agent_and_prompt_frontmatter_and_phase_names_match(self) -> None:
        for phase in self.phases:
            agent_text = (ROOT / phase["agent"]).read_text(encoding="utf-8")
            with self.subTest(phase=phase["id"]):
                self.assertRegex(frontmatter(agent_text), rf"(?m)^name: {re.escape(phase['id'])}$")
        run_text = (ROOT / ".github" / "prompts" / "run.prompt.md").read_text(encoding="utf-8")
        pr_text = (ROOT / ".github" / "prompts" / "pr.prompt.md").read_text(encoding="utf-8")
        self.assertRegex(frontmatter(run_text), r"(?m)^name: run$")
        self.assertRegex(frontmatter(run_text), r"(?m)^agent: orchestrator$")
        self.assertRegex(frontmatter(pr_text), r"(?m)^name: pr$")
        self.assertRegex(frontmatter(pr_text), r"(?m)^agent: pr$")

    def test_agent_ownership_and_approval_gate_match_manifest(self) -> None:
        bodies: set[str] = set()
        for phase in self.phases:
            path = ROOT / phase["agent"]
            text = path.read_text(encoding="utf-8")
            body = text.split("---", 2)[-1].strip()
            with self.subTest(phase=phase["id"]):
                self.assertEqual(allowed_files(text), phase["owns"])
                self.assertIn(f"Awaiting human approval. Run: python orchestrator.py approve {phase['id']} --by <your-name>", text)
                for protected in ("sdlc/", "orchestrator.py", "hooks/**", ".github/hooks/**"):
                    self.assertIn(protected, text)
                self.assertNotIn(body, bodies)
                bodies.add(body)

    def test_tools_are_scoped_to_roles(self) -> None:
        requirements = (ROOT / ".github" / "agents" / "requirements.agent.md").read_text(encoding="utf-8")
        architecture = (ROOT / ".github" / "agents" / "architecture.agent.md").read_text(encoding="utf-8")
        implementation = (ROOT / ".github" / "agents" / "implementation.agent.md").read_text(encoding="utf-8")
        review = (ROOT / ".github" / "agents" / "review.agent.md").read_text(encoding="utf-8")
        verify = (ROOT / ".github" / "agents" / "verify.agent.md").read_text(encoding="utf-8")
        pr = (ROOT / ".github" / "agents" / "pr.agent.md").read_text(encoding="utf-8")
        self.assertIn("vscode/askQuestions", requirements)
        self.assertIn("vscode/askQuestions", architecture)
        self.assertIn("search/usages", implementation)
        self.assertIn("search/usages", review)
        self.assertIn("search/changes", review)
        self.assertIn("search/changes", pr)
        self.assertIn("execute/testFailure", verify)
        self.assertNotIn("execute/testFailure", review)

    def test_pr_stage_b_uses_mcp_and_preserves_human_gate(self) -> None:
        agent = (ROOT / ".github" / "agents" / "pr.agent.md").read_text(encoding="utf-8")
        prompt = (ROOT / ".github" / "prompts" / "pr.prompt.md").read_text(encoding="utf-8")
        skill = (ROOT / ".github" / "skills" / "pr" / "SKILL.md").read_text(encoding="utf-8")
        for document in (agent, prompt, skill):
            with self.subTest(document=document[:40]):
                self.assertIn("explicit `go`", document)
                self.assertIn("create_branch", document)
                self.assertIn("push_files", document)
                self.assertIn("search_pull_requests", document)
                self.assertIn("create_pull_request", document)
                self.assertIn("pull_request_read", document)
                self.assertIn("base `main`", document)
                self.assertIn("Never merge", document)
                self.assertNotIn("git push -u origin", document)
                self.assertNotIn("sdlc/state.json", document)
        self.assertIn("draft: true", agent)
        self.assertIn("draft: true", skill)
        self.assertIn("Result: PASS", agent)
        self.assertIn("Result: PASS", skill)

    def test_skills_and_hook_registration(self) -> None:
        for skill in ("requirements", "verify", "pr"):
            text = (ROOT / ".github" / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(skill=skill):
                self.assertRegex(frontmatter(text), r"(?m)^user-invocable: false$")
        hook = json.loads((ROOT / ".github" / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        entry = hook["hooks"]["PreToolUse"][0]
        self.assertIn("hooks/guard.py", entry["command"])
        self.assertIn("hooks/guard.py", entry["windows"])

    def test_contract_phase_rows_match_manifest(self) -> None:
        contract = (ROOT / "docs" / "CONTRACT.md").read_text(encoding="utf-8")
        for phase in self.phases:
            with self.subTest(phase=phase["id"]):
                self.assertIn(f"| {phase['order']} | {phase['id']} |", contract)
                self.assertIn(f"`{phase['agent']}`", contract)
                self.assertIn(f"`{phase['prompt']}`", contract)
                for owned in phase["owns"]:
                    self.assertIn(f"`{owned}`", contract)


if __name__ == "__main__":
    unittest.main()
