Create environment: `uv venv -p 3.11 --seed`

Install: `uv pip install -e .`

Run MuJoCo simulation host to be accessed via `lerobot.robot.LekiwiClient`: `uv run lekiwi_sim_host`

Run standalone MuJoCo simulation: `uv run standalone_mujoco_sim`
