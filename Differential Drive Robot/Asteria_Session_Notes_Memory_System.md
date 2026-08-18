# Asteria Session Notes -- Memory System & Object-Oriented Design

## Progress

Completed: - Environment class (Version 1) - EnvironmentSnapshot class
design - Memory.remember_environment() design

## New Concepts

### 1. Class vs Object

A class is a blueprint. An object (instance) is a real entity created
from the class.

Example:

``` python
environment = Environment()
```

`Environment` is the class. `environment` is an object.

### 2. Objects Interact

Objects can be passed as arguments:

``` python
snapshot = EnvironmentSnapshot(environment)
```

The constructor receives the Environment object and copies its values.

### 3. self

`self` always refers to the current object being created or used.

Inside EnvironmentSnapshot: - `self` -\> EnvironmentSnapshot object -
`environment` -\> Environment object

### 4. Copying vs Referencing

Wrong:

``` python
self.last_environment = environment
```

Both variables point to the same object.

Correct: Create an EnvironmentSnapshot that copies the values. This
preserves history.

### 5. EnvironmentSnapshot

Purpose: Freeze the state of the environment at one instant.

Responsibilities: - Copy sensor values - Never update automatically -
Never create another snapshot inside **init**()

### 6. Constructor Responsibility

`__init__()` initializes one object only.

Do not create another instance of the same class inside its constructor
unless there is a very specific reason.

### 7. Memory Responsibilities

Memory decides WHAT to remember.

Responsibilities: - Store last environment snapshot - Store previous
environment snapshot - Store actions - Store experiences

### 8. Single Responsibility Principle

Environment: - Live sensor values

EnvironmentSnapshot: - Frozen copy

Memory: - Stores snapshots and experiences

### 9. remember_environment() Algorithm

1.  Move last_environment to previous_environment
2.  Create EnvironmentSnapshot from Environment
3.  Store it as last_environment

Example:

``` python
def remember_environment(self, environment):
    self.previous_environment = self.last_environment
    snapshot = EnvironmentSnapshot(environment)
    self.last_environment = snapshot
```

## Architecture

RobotConfig ├── Environment ├── EnvironmentSnapshot ├── Memory ├──
Decision Engine ├── Navigation ├── Motion Controller

## Key Takeaways

-   Think in terms of interacting objects, not isolated functions.
-   Each class should have one clear responsibility.
-   Pass objects between classes instead of duplicating logic.
-   Snapshots preserve history by copying values.

## Next Session

-   Build remember_action()
-   Design Action class
-   Build Experience objects
-   Complete Memory module
