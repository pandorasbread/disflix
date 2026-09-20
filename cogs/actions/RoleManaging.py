from cogs.actions.BaseAction import BaseAction
from discord import Message


class RoleManaging(BaseAction):
    async def addrole(self, content: str, msg: Message, rolename: str):
        server = msg.guild

        if content.strip('<>&@').isdecimal():
            role_id = int(content.strip('<>&@'))
        else:
            roles = await server.fetch_roles()
            while len(roles) > 0:
                r = roles.pop()
                if r.name == content:
                    role_id = r.id
                    break
        if (role_id is None):
            return await msg.channel.send('ERROR: invalid role ' + content)

        result = ""

        role = self.db.roles.find_one({"server_id": msg.guild.id, "role": rolename})
        if role is None:
            self.db.roles.insert_one({"server_id": msg.guild.id, "role": rolename, "role_id": role_id})
        else:
            self.db.roles.update_one({"server_id": msg.guild.id, "role": rolename}, {"$set": {"role_id": role_id}})
            return await msg.channel.send(
                rolename + " changed from " + server.get_role(role.get("role_id")).name + " to " + server.get_role(
                    role_id).name + '. ')

        return await msg.channel.send(rolename + " is now assigned to " + server.get_role(role_id).name + '.')
