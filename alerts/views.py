from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import Alert
from .serializers import AlertSerializer


class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Alert.objects.all()
        resolved = self.request.query_params.get("resolved")
        if resolved is not None:
            queryset = queryset.filter(is_resolved=(resolved.lower() == "true"))
        return queryset

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        alert = self.get_object()
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.save()
        return Response(AlertSerializer(alert).data)

    @action(detail=False, methods=["post"], url_path="run-checks")
    def run_checks(self, request):
        from .services import (
            check_reorder_levels, check_critical_threshold,
            check_out_of_stock, check_expiry_alerts, check_abnormal_movements,
        )
        results = {
            "reorder": check_reorder_levels(),
            "critical": check_critical_threshold(),
            "out_of_stock": check_out_of_stock(),
            "expiry": check_expiry_alerts(),
            "abnormal_movement": check_abnormal_movements(),
        }
        return Response({"created": results, "total": sum(results.values())})