from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, int_pk, uuid_field

if TYPE_CHECKING:
    from app.users.models import User
    from app.recipes.models import Recipe


class UserFavoriteRecipe(Base):
    __tablename__ = "user_favorite_recipes"
    __table_args__ = (
        UniqueConstraint('user_id', 'recipe_id', name='uq_user_favorite_recipe'),
    )

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), nullable=False)

    # Связи
    user: Mapped["User"] = relationship("User", back_populates="favorite_recipes")
    recipe: Mapped["Recipe"] = relationship("Recipe", back_populates="favorited_by_users")

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, user_id={self.user_id}, recipe_id={self.recipe_id})"

    def to_dict(self):
        return {
            "uuid": str(self.uuid),
            "user_uuid": str(self.user.uuid) if self.user else None,
            "recipe_uuid": str(self.recipe.uuid) if self.recipe else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }




















