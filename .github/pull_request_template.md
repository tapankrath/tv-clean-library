## What this changes

<!-- New model / fix to a list / playbook update / tool change -->

## For a new model (`community/<platform>/<brand-model>/`)

- [ ] `debloat.txt` header names the model, `ro.product.model`, firmware build, the date, and says what was kept and why
- [ ] Every line is `pm disable-user` safe: nothing uninstalled, no core Android packages
- [ ] Applied in batches and reboot-checked; Home, inputs, remote, keyboard, sound, Wi-Fi all work
- [ ] Used the TV for at least a few days since (say how many: __ )
- [ ] `tv.json` has `tv`, `os`, `brand`, `notes`

## For a playbook change

- [ ] Model, model year and firmware the new path was checked on: __

CI rebuilds the index and runs `tools/validate.py` and the fake-TV test on this PR.
