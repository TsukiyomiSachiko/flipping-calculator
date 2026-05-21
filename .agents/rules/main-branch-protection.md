---
trigger: always_on
---

When starting work on a new feature or optimization, switch to a new git branch that you name appropriately
Examples of good branch names are:
* feature/cashflow-management
* improvement/optimizing-api-response
* security/patching-sql-injection

When finishing work commit your changes under an appropriate name and push them to the new branch.

When refining on work you just produced, remain in the branch you made for it

When in doubt on whether to create a new feature branch, ask the user if they want to have a new branch created

Always checkout your new branch from main, so we can work on multiple features concurrently

Important: When you receive a prompt, make sure the branch you're working on is still up-to-date with main, if it's not, update it.