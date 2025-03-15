from django.http import HttpResponse


def index(request):
    return HttpResponse("Главная")


def about(request):
    return HttpResponse("О сайте")


def contact(request):
    return HttpResponse("Контакты")