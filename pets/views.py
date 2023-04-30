from django.shortcuts import render
from rest_framework.views import APIView, Request, status
from rest_framework.response import Response
from .models import Pet
from .serializers import PetSerializer
from rest_framework.pagination import PageNumberPagination
from traits.models import Trait
from groups.models import Group
from django.shortcuts import get_object_or_404


class PetView(APIView, PageNumberPagination):
    def get(self, request: Request):
        trait_param = request.query_params.get("trait")

        if trait_param:
            pets = Pet.objects.filter(traits__name=trait_param).all()
            print(pets)
            serializer = PetSerializer(pets, many=True)

        else:
            pets = Pet.objects.all()

        result_page = self.paginate_queryset(pets, request, view=self)

        serializer = PetSerializer(result_page, many=True)

        return self.get_paginated_response(serializer.data)

    def post(self, request: Request):
        serializer = PetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pet_group = serializer.validated_data.pop("group")
        pet_traits = serializer.validated_data.pop("traits")

        group_obj = Group.objects.filter(scientific_name__iexact=pet_group["scientific_name"]).first()

        if not group_obj:
            group_obj = Group.objects.create(**pet_group)

        pet = Pet.objects.create(**serializer.validated_data, group=group_obj)

        for trait in pet_traits:
            trait_obj = Trait.objects.filter(name__iexact=trait["name"]).first()

            if not trait_obj:
                trait_obj = Trait.objects.create(**trait)

            pet.traits.add(trait_obj)

        serializer = PetSerializer(pet)

        return Response(serializer.data, status.HTTP_201_CREATED)


class PetDetailView(APIView):
    def get(self, request: Request, pet_id):
        pet = get_object_or_404(Pet, id=pet_id)
        serializer = PetSerializer(pet)

        return Response(serializer.data)

    def patch(self, request: Request, pet_id: int):
        pet = get_object_or_404(Pet, id=pet_id)

        serializer = PetSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        traits_data = serializer.validated_data.pop("traits", None)
        group_data = serializer.validated_data.pop("group", None)

        for key, value in serializer.validated_data.items():
            setattr(pet, key, value)

        if traits_data:
            for trait in traits_data:
                trait_obj = Trait.objects.filter(name__iexact=trait["name"])

                if trait_obj:
                    pet.traits.set(trait_obj)
                else:
                    trait_obj = Trait.objects.create(**trait)
                    trait_list = []
                    trait_list.append(trait_obj)
                    pet.traits.set(trait_list)

        if group_data:
            group_obj = Group.objects.filter(scientific_name__iexact=group_data["scientific_name"])

            if group_obj:
                pet.group.scientific_name = group_obj
            else:
                group_obj = Group.objects.create(**group_data)
                pet.group = group_obj

        pet.save()
        serializer = PetSerializer(pet)
        return Response(serializer.data)

    def delete(self, request: Request, pet_id):
        pet = get_object_or_404(Pet, id=pet_id)
        pet.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)