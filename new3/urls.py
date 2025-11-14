from django.contrib import admin
from django.urls import path, include
from blog.views import home  # blog 앱의 home 뷰 가져오기
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('blog/', include('blog.urls')),  # 회원 관리 URL 포함
    path('', include('blog.urls')),
]
