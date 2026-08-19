# Permissions and Approval

| Action | Risk | Automatic? | Approval required | Rollback |
|---|---|---|---|---|
| Read project files | Low | Yes | No | Not required |
| Run tests in sandbox | Low | Yes | No | Destroy sandbox |
| Create branch | Medium | Project-specific | Usually | Delete branch |
| Publish publicly | High | No | Yes | Delete or correct post |
| Deploy production | High | No | Yes | Roll back deployment |
| Delete data | High | No | Yes | Restore backup |

## Project-specific rules

TBD
