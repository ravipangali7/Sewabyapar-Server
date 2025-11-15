"""
Template generator script for creating admin panel templates
Run this script to generate all missing templates
"""
import os

TEMPLATE_BASE = {
    'list': """{% extends 'admin/layouts/base.html' %}
{% load static %}

{% block content %}
<div class="container-fluid p-0">
    <div class="mb-3">
        <h1 class="h3 d-inline align-middle">{title}</h1>
        <a class="btn btn-primary ms-2" href="{% url '{create_url}' %}">
            <i class="align-middle" data-feather="plus"></i> Add {model_name}
        </a>
    </div>
    <div class="row">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h5 class="card-title mb-0">All {title}</h5>
                </div>
                <div class="card-body">
                    <form method="get" class="mb-3">
                        <div class="input-group">
                            <input type="text" class="form-control" name="search" placeholder="Search..." value="{{ search }}">
                            <button class="btn btn-primary" type="submit">Search</button>
                        </div>
                    </form>
                    <table class="table table-hover">
                        <thead>
                            {table_headers}
                        </thead>
                        <tbody>
                            {% for item in {object_list} %}
                            <tr>
                                {table_rows}
                            </tr>
                            {% empty %}
                            <tr>
                                <td colspan="{colspan}" class="text-center">No items found</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                    {% if is_paginated %}
                    <nav>
                        <ul class="pagination">
                            {% if page_obj.has_previous %}
                                <li class="page-item"><a class="page-link" href="?page={{ page_obj.previous_page_number }}">Previous</a></li>
                            {% endif %}
                            <li class="page-item active"><span class="page-link">Page {{ page_obj.number }} of {{ page_obj.paginator.num_pages }}</span></li>
                            {% if page_obj.has_next %}
                                <li class="page-item"><a class="page-link" href="?page={{ page_obj.next_page_number }}">Next</a></li>
                            {% endif %}
                        </ul>
                    </nav>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}""",
    
    'detail': """{% extends 'admin/layouts/base.html' %}
{% load static %}

{% block content %}
<div class="container-fluid p-0">
    <div class="mb-3">
        <h1 class="h3 d-inline align-middle">{title} Details</h1>
        <a class="btn btn-primary ms-2" href="{% url '{update_url}' {object}.pk %}">Edit</a>
        <a class="btn btn-danger ms-2" href="{% url '{delete_url}' {object}.pk %}">Delete</a>
        <a class="btn btn-secondary ms-2" href="{% url '{list_url}' %}">Back to List</a>
    </div>
    <div class="row">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h5 class="card-title mb-0">{title} Information</h5>
                </div>
                <div class="card-body">
                    {detail_fields}
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}""",
    
    'form': """{% extends 'admin/layouts/base.html' %}
{% load static %}

{% block content %}
<div class="container-fluid p-0">
    <div class="mb-3">
        <h1 class="h3 d-inline align-middle">{title}</h1>
        <a class="btn btn-secondary ms-2" href="{% url '{list_url}' %}">Back to List</a>
    </div>
    <div class="row">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h5 class="card-title mb-0">{form_title}</h5>
                </div>
                <div class="card-body">
                    <form method="post" enctype="multipart/form-data">
                        {% csrf_token %}
                        {form_fields}
                        <div class="mt-3">
                            <button type="submit" class="btn btn-primary">Save</button>
                            <a href="{% url '{list_url}' %}" class="btn btn-secondary">Cancel</a>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}""",
    
    'delete': """{% extends 'admin/layouts/base.html' %}
{% load static %}

{% block content %}
<div class="container-fluid p-0">
    <div class="row">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h5 class="card-title mb-0">Confirm Delete</h5>
                </div>
                <div class="card-body">
                    <p>Are you sure you want to delete this {model_name}?</p>
                    <form method="post">
                        {% csrf_token %}
                        <button type="submit" class="btn btn-danger">Yes, Delete</button>
                        <a href="{% url '{list_url}' %}" class="btn btn-secondary">Cancel</a>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}"""
}

# This is a helper script - templates should be created manually or via a more sophisticated generator
# For now, we'll create the essential templates manually

