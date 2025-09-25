{{- define "railway-crossing.name" -}}
railway-crossing
{{- end }}

{{- define "railway-crossing.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "railway-crossing.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{- define "railway-crossing.labels" -}}
app.kubernetes.io/name: {{ include "railway-crossing.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
app.kubernetes.io/managed-by: Helm
{{- end }}