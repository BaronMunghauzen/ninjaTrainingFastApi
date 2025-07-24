import asyncio
from app.database import async_session_maker
from app.files.models import File
from app.users.models import User
from app.users.dao import UsersDAO
from sqlalchemy import select, update

async def debug_file_deletion():
    """Debug script to check file and user references"""
    async with async_session_maker() as session:
        # Check the specific file
        file_uuid = '4886dede-21a6-4135-99c6-d8facab6b524'
        query = select(File).where(File.uuid == file_uuid)
        result = await session.execute(query)
        file_record = result.scalar_one_or_none()
        
        if file_record:
            print(f"File found:")
            print(f"  ID: {file_record.id}")
            print(f"  UUID: {file_record.uuid}")
            print(f"  Entity type: {file_record.entity_type}")
            print(f"  Entity ID: {file_record.entity_id}")
        else:
            print(f"File with UUID {file_uuid} not found")
            return
        
        # Check all users that reference this file
        query = select(User).where(User.avatar_id == file_record.id)
        result = await session.execute(query)
        users = result.scalars().all()
        
        print(f"\nUsers referencing this file as avatar:")
        for user in users:
            print(f"  User ID: {user.id}")
            print(f"  User UUID: {user.uuid}")
            print(f"  Avatar ID: {user.avatar_id}")
        
        if not users:
            print("  No users found referencing this file")
        else:
            # Try to update the user's avatar_id to None
            print(f"\nAttempting to update user {users[0].uuid} avatar_id to None...")
            try:
                await UsersDAO.update(users[0].uuid, avatar_id=None)
                print("User update successful!")
                
                # Check if the update worked
                query = select(User).where(User.id == users[0].id)
                result = await session.execute(query)
                updated_user = result.scalar_one_or_none()
                if updated_user:
                    print(f"Updated user avatar_id: {updated_user.avatar_id}")
                else:
                    print("User not found after update")
                
            except Exception as e:
                print(f"User update failed: {e}")
        
        # Check all files
        query = select(File)
        result = await session.execute(query)
        all_files = result.scalars().all()
        
        print(f"\nAll files in database:")
        for file in all_files:
            print(f"  File ID: {file.id}, UUID: {file.uuid}, Entity: {file.entity_type}:{file.entity_id}")
        
        # Check all users with avatar_id
        query = select(User).where(User.avatar_id.isnot(None))
        result = await session.execute(query)
        users_with_avatars = result.scalars().all()
        
        print(f"\nAll users with avatar_id:")
        for user in users_with_avatars:
            print(f"  User ID: {user.id}, Avatar ID: {user.avatar_id}")

if __name__ == "__main__":
    asyncio.run(debug_file_deletion()) 