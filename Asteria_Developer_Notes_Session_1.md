# Asteria Developer Notes -- Session: Environment, Snapshots, Memory & OOP

## Session Goals

-   Finalize the Environment module.
-   Design EnvironmentSnapshot.
-   Begin the Memory module.
-   Understand core object-oriented programming concepts.

# 1. Class vs Object

A **class** is a blueprint describing what an object should contain.

Example:

``` python
class Environment:
    ...
```

An **object** (instance) is created from that blueprint.

``` python
environment = Environment()
```

Here `Environment` is the class and `environment` is the object.

------------------------------------------------------------------------

# 2. The `self` Keyword

`self` always refers to **the current object**.

Inside:

``` python
class EnvironmentSnapshot:
    def __init__(self, environment):
```

-   `self` → the new EnvironmentSnapshot object.
-   `environment` → the Environment object passed into the constructor.

Example:

``` python
self.temperature = environment.temperature
```

means:

> Read the temperature from the Environment object and store it inside
> this EnvironmentSnapshot object.

------------------------------------------------------------------------

# 3. Objects as Parameters

Objects can be passed to methods and constructors.

``` python
snapshot = EnvironmentSnapshot(environment)
```

This passes the Environment object to the constructor.

------------------------------------------------------------------------

# 4. Copy vs Reference

Reference:

``` python
self.last_environment = environment
```

Both names point to the same object.

Copy:

``` python
self.last_environment = EnvironmentSnapshot(environment)
```

Creates an independent object that preserves history.

------------------------------------------------------------------------

# 5. Why EnvironmentSnapshot Exists

Environment stores **live** sensor values.

Memory needs a **frozen** copy.

EnvironmentSnapshot copies values once and never changes automatically.

------------------------------------------------------------------------

# 6. Encapsulation

## Definition

Encapsulation means bundling related data and behaviour into one class
while giving that class a clear responsibility.

## How we used it

Environment - Owns live sensor values.

EnvironmentSnapshot - Owns the logic for freezing the environment.

Memory - Owns the logic for remembering.

Each class hides its implementation from the others.

Benefits: - Modular code - Easier maintenance - Easier testing - Lower
coupling

------------------------------------------------------------------------

# 7. Single Responsibility Principle

Each class should have one primary responsibility.

Environment -\> live world

EnvironmentSnapshot -\> frozen world

Memory -\> remembering

------------------------------------------------------------------------

# 8. Constructor Responsibility

A constructor should initialize **one object only**.

Incorrect:

Creating another EnvironmentSnapshot inside
EnvironmentSnapshot.\_\_init\_\_() causes infinite recursion.

Correct:

Create snapshots outside the class when Memory decides to remember.

------------------------------------------------------------------------

# 9. Memory Design

Current attributes:

``` python
class Memory:
    def __init__(self):
        self.last_environment = None
        self.previous_environment = None
        self.last_action = None
        self.previous_action = None
        self.experience_list = []
```

Purpose: - Store snapshots - Store actions - Store experiences

------------------------------------------------------------------------

# 10. remember_environment()

Algorithm

1.  Preserve previous snapshot.
2.  Create a new EnvironmentSnapshot.
3.  Store it as last_environment.

Implementation:

``` python
def remember_environment(self, environment):
    self.previous_environment = self.last_environment
    snapshot = EnvironmentSnapshot(environment)
    self.last_environment = snapshot
```

------------------------------------------------------------------------

# 11. Current Architecture

RobotConfig ├── Environment ├── EnvironmentSnapshot ├── Memory ├──
DecisionEngine (future) ├── Navigation (future) ├── MotionController
(future)

------------------------------------------------------------------------

# Common Mistakes

-   Confusing classes with objects.
-   Passing references when a copy is needed.
-   Creating new objects recursively inside **init**().
-   Giving one class too many responsibilities.

------------------------------------------------------------------------

# Progress

Completed: - Environment ✔ - EnvironmentSnapshot ✔ - Memory foundation ✔

Next: - remember_action() - Action class - Experience class - Complete
Memory module
