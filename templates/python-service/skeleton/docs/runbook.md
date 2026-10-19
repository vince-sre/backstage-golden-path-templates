# Runbook: ${{ values.name }}

## Alerts
Multi-window burn-rate alerts, following the pattern in [k8s-observability-stack](https://github.com/vince-sre/k8s-observability-stack).

| Alert | Meaning | First step |
|---|---|---|
| `SLOErrorBudgetBurnFast{job="${{ values.name }}"}` | Error budget burning fast (2% in 1h) | Check the last deploy in Argo CD; roll back if it correlates |
| `SLOErrorBudgetBurnSlow{job="${{ values.name }}"}` | Sustained elevated errors | Look at dependency latency and 5xx by path on the dashboard |

## Common actions
- **Roll back:** revert the last tag bump in `${{ values.gitopsRepo }}` (`workloads/${{ values.name }}/values-<env>.yaml`).
- **Scale:** change `autoscaling.maxReplicas` in the same values file. Don't `kubectl scale`, because Argo CD self-heal will revert it.
- **Logs:** `kubectl -n team-${{ values.name }}-<env> logs deploy/${{ values.name }}`
