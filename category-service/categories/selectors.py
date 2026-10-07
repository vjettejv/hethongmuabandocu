from categories.models import Category


def all_categories():
    # Match Sequelize findAll: do not introduce ordering or pagination.
    return Category.objects.all()
