# Railway CSML files

- CSML 1.0
  - `railway.local.csml`: Default version (runs locally).
  - `railway.remote.csml`: Remote version. Used for the experiment on Grid`5000.
- CSML 2.0
  - `railway.pkl`: Default Pkl version.
  - `railway-job.pkl`: Default Pkl job description (Imports `railway.pkl`)
  - `railway-job-inline.pkl`: Pkl job description (Contains `railway.pkl` inline)

For CSML 2.0, `local` or `remote` can be selected via an environment variable (`RAILWAY_REMOTE`) stored on the device 
that runs the Cirrina runtime.