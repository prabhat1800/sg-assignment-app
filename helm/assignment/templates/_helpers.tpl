{{- define "assignment.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "assignment.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "assignment.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}