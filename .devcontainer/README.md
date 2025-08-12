# DevContainers

- [DevContainers](#devcontainers)
  - [Lekiwi-Dev](#lekiwi-dev)
      - [Image Details](#image-details)
      - [Getting Started](#getting-started)

## Lekiwi-Dev

#### Image Details

* Base Image: `jammy` (ubuntu)
* Rust:
  * Installed via rustup.
  * The rustc version is configured via `./lekiwi-dev/devcontainer.json` [1]

[1] Override if necessary. At a later date, we might configure the bazel version via a marker file at the project root.

#### Getting Started

Locally:

* [Install VSCode](https://code.visualstudio.com/docs/setup/linux#_debian-and-ubuntu-based-distributions)
* Install [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
* Open the project in VSCode
* CTRL-SHIFT-P &rarr; Reopen in Container
* Open a terminal in the container and run

```
(docker) dev@rust-dev:/workspaces/lekiwi-dora$ cargo build
```

CodeSpaces:

* Go to Codespaces
* Select `New with Options`
* Select `Lekiwi Dev` from the `Dev Container Configuration`

* Open a terminal in the container and run

```
@<github-username> ➜ /workspaces/rnd_lekiwi (main) $ cargo build
```
