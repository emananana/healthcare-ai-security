# Discord draft — copy and send yourself

Hey everyone! I simplified the repo instructions:
https://github.com/emananana/healthcare-ai-security

Clone/pull the repo, create your own branch, then give Claude or Codex **PROJECT_CONTEXT.md + your file in context/** (VANESSA.md, REYA.md or ZHAOTONG.md). Your file has ordered tasks, tests and a starter prompt. Review the changes and keep work in your assigned files.

My enterprise chatbot is already included in your local clone. Vanessa/Reya: use your own Groq key for local live tests; don't share or commit it. Reya can test hand-written events without a live red agent. Vanessa can test generated attacks independently and later against the enterprise chatbot with mock blue. Zhaotong can test SQLite/access checks without any LLM. Run the offline tests first; setup commands are in PROJECT_CONTEXT.md.

Shared app: https://healthcare-ai-security.onrender.com/
Username: cometcare; I'll send the team password privately. No API key is needed to visit. This shows our deployed main branch, not your local edits.

When ready, push your branch and open a PR. I'll review, connect and merge your module, then verify deployment. The shared server uses its existing Groq key—no need to send me yours. You don't need to wait for everyone else to finish!
