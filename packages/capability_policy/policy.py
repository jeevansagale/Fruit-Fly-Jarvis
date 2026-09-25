DEFAULT_ALLOWED={'workspace.next','workspace.previous','workspace.focus','app.launch','media.play_pause','media.next','media.previous'}
class CapabilityPolicy:
    def __init__(self, allowed=None): self.allowed=set(allowed or DEFAULT_ALLOWED)
    def validate(self, action, arguments):
        if action not in self.allowed: return False, 'capability not allowlisted'
        return True, 'validated'
