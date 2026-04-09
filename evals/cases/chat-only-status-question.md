# Case: chat-only-status-question

## Task Description
The user asks: "What does `git status` do?"

## Background
- no code change is requested
- no file read is requested
- no command execution is required to answer correctly
- this case exists to ensure the system does not over-trigger workflow for pure explanation

## Expected Triage
- chat-only direct answer
- no `dtt-change-triage` execution
- no lane selection
- no downstream agent dispatch

## Why This Is Correct
The request is purely informational and does not ask the system to perform work.

## Misclassification Risks
- unnecessary workflow routing for a pure question
- wasted cost on triage and delegation

## Manual Review Checks
- verify that the response stays direct and explanatory
- verify that no workflow summary is produced
- verify that the response includes the chat-only marker when your environment requires it
