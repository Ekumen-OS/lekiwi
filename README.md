# rnd_lekiwi

## :globe_with_meridians: Description

TODO

## Prerequisites

TODO

## Platforms

 - OS:
   - Ubuntu 22.04 Jammy Jellyfish

## :package: Project structure

TODO

## :pick: Workspace setup

Refer to [.devcontainer/README.md](.devcontainer/README.md)

## :gear: Build

### Build systems

This repository combines both `rust` and `python` packages. `cargo` and `uv` are the tools of choice.

#### Rust packages

 - Building `rust` packages:
    ```
    cargo build
    ```

#### Python packages
 - Setup a `venv` within `andino-rs` folder.
    ```
    uv venv -p 3.11 --seed
    ```

 - Building `python` packages:
    ```
    uv build --all-packages
    ```

## *`dora`* Integration

What is dora? See https://dora-rs.ai/

TODO


### Appendix

## :raised_hands: Contributing

Issues or PRs are always welcome! Please refer to [CONTRIBUTING](CONTRIBUTING.md) doc.

## Code development

 - Workspace setup: Refer to [.devcontainer/README.md](.devcontainer/README.md)
 - This repository uses `pre-commit`.
    - To add it to git's hook, use:
     ```
     pip install pre-commit
     pre-commit install
     ```
    - Every time a commit is attempted, pre-commit will run. The checks can be by-passed by adding `--no-verify` to *git commit*, but take into account pre-commit also runs as a required Github Actions check, so you will need it to pass.
