from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.views.decorators.http import require_http_methods
from rest_framework import serializers

from .models import DrugInteraction


class DrugInteractionSerializer(serializers.ModelSerializer):
    drug1 = serializers.CharField(source='drug_a')
    drug2 = serializers.CharField(source='drug_b')
    action = serializers.CharField(source='management', allow_blank=True, required=False)

    class Meta:
        model = DrugInteraction
        fields = ['id', 'drug1', 'drug2', 'severity', 'description', 'action', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET", "POST"])
def drug_interactions_list_create_api(request):
    if request.method == 'GET':
        interactions = DrugInteraction.objects.all().order_by('-created_at')
        serializer = DrugInteractionSerializer(interactions, many=True)
        return Response({'count': interactions.count(), 'results': serializer.data}, status=status.HTTP_200_OK)

    if request.user.role != 'ADMIN':
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    serializer = DrugInteractionSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response({'detail': 'Validation error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET", "PATCH", "DELETE"])
def drug_interaction_detail_api(request, interaction_id):
    try:
        interaction = DrugInteraction.objects.get(id=interaction_id)
    except DrugInteraction.DoesNotExist:
        return Response({'detail': 'Interaction not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(DrugInteractionSerializer(interaction).data, status=status.HTTP_200_OK)

    if request.user.role != 'ADMIN':
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'DELETE':
        interaction.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = DrugInteractionSerializer(interaction, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response({'detail': 'Validation error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
