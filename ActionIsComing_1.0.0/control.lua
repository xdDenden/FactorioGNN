-- control.lua
local json = require("json")

ai_research_index = 1

local AI_START_TECHS = {
    ["steam-power"] = true,
    ["electronics"] = true,
    ["automation-science-pack"] = true
}

local AI_RESEARCH_QUEUE = {
    "automation",
    "electric-mining-drill",
    "logistics",
    "logistic-science-pack",
    "fast-inserter",
    "steel-processing",
    "engine",
    "automation-2",
    "fluid-handling",
    "oil-gathering",
    "oil-processing",
    "plastics",
    "advanced-circuit"
}

local moving_characters = {}

local buildings = {
  "wooden-chest",
  "storage-tank",
  "transport-belt",
  "fast-transport-belt",
  "underground-belt",
  "fast-underground-belt",
  "splitter",
  "fast-splitter",
  "burner-inserter",
  "inserter",
  "long-handed-inserter",
  "fast-inserter",
  "bulk-inserter",
  "small-electric-pole",
  "medium-electric-pole",
  "big-electric-pole",
  "pipe",
  "pipe-to-ground",
  "boiler",
  "steam-engine",
  "burner-mining-drill",
  "electric-mining-drill",
  "offshore-pump",
  "pumpjack",
  "stone-furnace",
  "steel-furnace",
  "assembling-machine-1",
  "assembling-machine-2",
  "oil-refinery",
  "chemical-plant",
  "lab"
}

-- Item-Liste
local item_list = {
    [0] = "none",
    [1] = "wooden-chest",
    [2] = "storage-tank",
    [3] = "transport-belt",
    [4] = "fast-transport-belt",
    [5] = "underground-belt",
    [6] = "fast-underground-belt",
    [7] = "splitter",
    [8] = "fast-splitter",
    [9] = "burner-inserter",
    [10] = "inserter",
    [11] = "long-handed-inserter",
    [12] = "fast-inserter",
    [13] = "bulk-inserter",
    [14] = "small-electric-pole",
    [15] = "medium-electric-pole",
    [16] = "big-electric-pole",
    [17] = "pipe",
    [18] = "pipe-to-ground",
    [19] = "boiler",
    [20] = "steam-engine",
    [21] = "burner-mining-drill",
    [22] = "electric-mining-drill",
    [23] = "offshore-pump",
    [24] = "pumpjack",
    [25] = "stone-furnace",
    [26] = "steel-furnace",
    [27] = "assembling-machine-1",
    [28] = "assembling-machine-2",
    [29] = "oil-refinery",
    [30] = "chemical-plant",
    [31] = "lab",
    [32] = "iron-plate",
    [33] = "copper-plate",
    [34] = "steel-plate",
    [35] = "plastic-bar",
    [36] = "sulfur",
    [37] = "iron-gear-wheel",
    [38] = "iron-stick",
    [39] = "copper-cable",
    [40] = "electronic-circuit",
    [41] = "advanced-circuit",
    [42] = "engine-unit",
    [43] = "automation-science-pack",
    [44] = "logistic-science-pack",
    [45] = "chemical-science-pack",
    [46] = "wood",
    [47] = "coal",
    [48] = "stone",
    [49] = "iron-ore",
    [50] = "copper-ore",
    [51] = "stone-brick",
    [52] = "basic-oil-processing"
}


local recipe_exclude = {
    [46] = true,  -- wood
    [49] = true,  -- iron-ore
    [50] = true,  -- copper-ore
    [47] = true,  -- coal
    [48] = true,  -- stone
    -- Füge hier weitere IDs hinzu die keine Rezepte sind
}

-- DANN die Exclude-Liste
local craft_exclude = {
    [0] = true,  -- none
    [46] = true,  -- wood
    [49] = true,  -- iron-ore
    [50] = true,  -- copper-ore
    [47] = true,  -- coal
    [48] = true,  -- stone
}

local insert_exclude = {
    [52] = true,  -- basic-oil-processing
}

script.on_init(function()
    gameinit()
end)

--create new force
function gameinit()
    local force_name = "AI"
    local surface = game.surfaces[1]
    if not game.forces[force_name] then
        local new_force = game.create_force(force_name)
    end

    --Spawn in New Character at the start of the Game
    local character = game.surfaces[1].create_entity{
        name = "character",
        position = {x = 0, y = 0},
        force = "AI"
    }

    global.ai_research_queue = AI_RESEARCH_QUEUE
    global.ai_research_index = 1
    global.ai_research_max_queue = 5
end

--Build something and remove it out of the characters inventory command
--/build x y <index(1-31)> <direction(0-3)>
--Build something and remove it out of the characters inventory command
--/build x y <index(1-31)> <direction(0-3)>
commands.add_command("build", "", function(event)
  local surface = game.surfaces[1]

  local params = {}
  for param in string.gmatch(event.parameter or "", "%S+") do
    table.insert(params, param)
  end

  local x = tonumber(params[1])
  local y = tonumber(params[2])
  local index = tonumber(params[3])
  local dir_input = tonumber(params[4]) or 0

  -- Maps input 0-3 to specific Factorio direction integers
  local direction_map = {
    [0] = 0,   -- Input 0 -> 0
    [1] = 4,   -- Input 1 -> 4
    [2] = 8,   -- Input 2 -> 8
    [3] = 12   -- Input 3 -> 12
  }

  -- Select direction from map, default to 0 if input is weird
  local direction = direction_map[dir_input] or 0

  local building = buildings[index]

  if not building then
    game.print("Invalid index!")
    return
  end

  local characters = surface.find_entities_filtered{
    name = "character",
    force = "AI"
  }

  local character = characters[1]

  -- Safety check if character exists
  if not character then
    game.print("No AI character found")
    return
  end

  local item_count = character.get_item_count(building)

  if item_count < 1 then
    game.print("char has no " .. building .. " in the inventory")
    return
  end

  local pos = {x, y}

  if surface.can_place_entity{name = building, position = pos, force = "AI", direction = direction,build_check_type=defines.build_check_type.manual} then

    --remove item out of the inventory of the character
    character.remove_item{name = building, count = 1}

    --method to create the entity
    surface.create_entity{
      name = building,
      position = pos,
      force = "AI",
      direction = direction
    }

    game.print("Built " .. building .. " (Remaining: " .. (item_count - 1) .. ") Direction val: " .. direction)
  else
    game.print("you can't place there")
  end
end)

commands.add_command("rotate", "Rotate building at position: /rotate <x> <y> <direction(0-3)>", function(event)
    local params = {}
    for param in string.gmatch(event.parameter or "", "%S+") do
        table.insert(params, param)
    end

    local x = tonumber(params[1])
    local y = tonumber(params[2])
    local dir_input = tonumber(params[3]) or 0

    -- 1. NEW: Direction Map Logic
    local direction_map = {
        [0] = 0,   -- Input 0 -> 0 (North)
        [1] = 4,   -- Input 1 -> 4 (South for 8-way, or East for 16-way)
        [2] = 8,   -- Input 2 -> 8
        [3] = 12   -- Input 3 -> 12
    }

    -- Default to 0 if input is invalid
    local direction = direction_map[dir_input] or 0

    local surface = game.surfaces[1]

    -- Find entity at position
    local entities = surface.find_entities_filtered{
        position = {x, y},
        radius = 0.5
    }

    if #entities == 0 then
        game.print("No entity found at (" .. x .. ", " .. y .. ")")
        return
    end

    -- Usually, the first entity found is the building, but sometimes it might be a ghost or item-on-ground
    -- It is often safer to grab the first one that supports direction
    local entity = entities[1]

    if not entity.supports_direction then
        game.print(entity.name .. " is not rotatable!")
        return
    end

    -- 2. FIX: Actually apply the direction to the entity
    entity.direction = direction

    game.print("Rotated " .. entity.name .. " at (" .. x .. ", " .. y .. ") to direction val: " .. direction)
end)

--Spawn a new Character(AI)
--/spawn
commands.add_command("spawn", "", function(event)
    local surface = game.surfaces[1]

    local character = game.surfaces[1].create_entity{
        name = "character",
        position = {x = 0, y = 0},
        force = "AI"
    }
end)

--mine something and put the items into the characters inventory
--/mine x y
commands.add_command("mine", "", function(event)
    local params = {}
    for word in event.parameter:gmatch("%S+") do
        table.insert(params, tonumber(word))
    end

    local x = params[1] or 0
    local y = params[2] or 0

    --find the character
    local character = game.surfaces[1].find_entities_filtered{
        name = "character",
        force = "AI"
    }[1]

    --find the entity we want to mine
    local entity = game.surfaces[1].find_entities_filtered{
        position = {x, y},
        radius = 1
    }[1]

    if character and entity then
        character.mine_entity(entity, true)
        game.print("char mined at " .. x .. ", " .. y)
    end
end)

--makes the character move to a point
--/moveto x y
commands.add_command("moveto", "", function(event)
    local params = {}
    for word in event.parameter:gmatch("%S+") do
        table.insert(params, tonumber(word))
    end

    local target_x = math.floor(params[1] or 0)
    local target_y = math.floor(params[2] or 0)

    local character = game.surfaces[1].find_entities_filtered{
        name = "character",
        force = "AI"
    }[1]

    if character then
        moving_characters[character.unit_number] = {
            character = character,
            target = {x = target_x, y = target_y}
        }

        game.print("char walks to: " .. target_x .. ", " .. target_y)
    end
end)

--Move Logic
--on_tick
--First walk to the X coord till near atleast 1 tile the dest
--Then walk to the Y coord till near atleast 1 tile the dest
--If near then TP to the dest x y
script.on_event(defines.events.on_tick, function(event)
    for id, data in pairs(moving_characters) do
        local character = data.character
        local target = data.target

        if character and character.valid then
            local char_x = math.floor(character.position.x)
            local char_y = math.floor(character.position.y)

            --game.print("Character: " .. char_x .. "," .. char_y .. " | Ziel: " .. target.x .. "," .. target.y)

            local diff_x = math.abs(char_x - target.x)
            local diff_y = math.abs(char_y - target.y)

            --arrived at location?
            if diff_x <= 1 and diff_y <= 1 then
                moving_characters[id] = nil
                character.teleport({x = target.x + 0.5, y = target.y + 0.5})
                character.walking_state = {walking = false}
                game.print("arrived at position")

            else
                local direction

                --X
                if diff_x > 1 then
                    if target.x < char_x then
                        direction = defines.direction.west
                    else
                        direction = defines.direction.east
                    end
                --Y
                elseif diff_y > 1 then
                    if target.y < char_y then
                        direction = defines.direction.north
                    else
                        direction = defines.direction.south
                    end
                end

                character.walking_state = {walking = true, direction = direction}
            end
        end
    end
end)

--gives the character an item from the index (for debug)
--/give <itemindex(1-52)> <amount>
commands.add_command("give", "", function(event)
    local surface = game.surfaces[1]
    --local player = game.get_player(event.player_index)

    local characters = surface.find_entities_filtered{
        name = "character",
        force = "AI"
    }

    local character = characters[1]

    local params = {}
    for word in string.gmatch(event.parameter, "%S+") do
        table.insert(params, word)
    end

    -- Verarbeite Paare von ID und Count
    for i = 1, #params, 2 do
        local id = tonumber(params[i])
        local count = tonumber(params[i + 1])

        if id and count and item_list[id] then
            --give item method
            local inserted = character.insert{name = item_list[id], count = count}
            game.print("Gave Char: " .. inserted .. "x " .. item_list[id])
        else
            game.print("Invalid itemparams: " .. (params[i] or "nil") .. " " .. (params[i + 1] or "nil"))
        end
    end
end)

--Let the character craft an item
--/craft <itemindex(1-52)> <amount>
commands.add_command("craft", "", function(event)
    local surface = game.surfaces[1]

    local characters = surface.find_entities_filtered{
        name = "character",
        force = "AI"
    }

    local character = characters[1]

    local params = {}
    for word in string.gmatch(event.parameter or "", "%S+") do
        table.insert(params, word)
    end

    if #params < 2 then
        game.print("Usage: /craft <recipe_id> <count>")
        return
    end

    local recipe_id = tonumber(params[1])
    local count = tonumber(params[2])

    if not recipe_id or not count then
        game.print("Invalid craftparam")
        return
    end

    if craft_exclude[recipe_id] then
        game.print("Item ID " .. recipe_id .. " cannot be crafted!")
        return
    end

    if not item_list[recipe_id] then
        game.print("Invalid recipe ID!")
        return
    end

    local recipe_name = item_list[recipe_id]

    -- Check if recipe is researched
    local ai_force = game.forces["AI"]
    local recipe = ai_force.recipes[recipe_name]

    if not recipe or not recipe.enabled then
        game.print("Recipe " .. recipe_name .. " not researched yet!")
        return
    end

    --crafting method
    local crafted = character.begin_crafting{recipe = recipe_name, count = count}

    if crafted > 0 then
        game.print("char crafts " .. crafted .. "x " .. recipe_name)
    else
        game.print("no materials")
    end
end)

--Gives character information
--Position and Inventory
-- Gives character information
-- Position and Inventory
commands.add_command("char_info", "", function(event)
  local surface = game.surfaces[1]

  -- Find AI Character
  local ai_characters = surface.find_entities_filtered{
    name = "character",
    force = "AI"
  }

  if #ai_characters == 0 then
    -- Return an empty/error object as JSON
    local error_response = json.encode({status = "FAILED", message = "No AI Character found."})
    rcon.print(error_response)
    return
  end

  local character = ai_characters[1]
  local pos = character.position
  local inventory = character.get_main_inventory()

  -- Data container to return
  local result = {
    pos = {x = pos.x, y = pos.y},
    inventory = {}
  }

  if inventory and not inventory.is_empty() then
    local slot_count = #inventory

    for i = 1, slot_count do
      local stack = inventory[i]
      if stack.valid_for_read then
        local name = stack.name
        local count = stack.count

        -- Collect items into a single list of objects (better for Python parsing)
        table.insert(result.inventory, {name = name, count = count})
      end
    end
  end

  -- Encode to JSON string and print via rcon
  local json_result = helpers.table_to_json(result)
  rcon.print(json_result)
end)

--Insert items from the character into a machine
--/insert x y <itemindex(1-52)> <amount>
commands.add_command("insert_into", "AI Character inserts items into machine: /insert <item_id> <count> <x> <y>", function(event)
    --local player = game.players[event.player_index]
    local surface = game.surfaces[1]

    -- Parse Parameter
    local params = {}
    for param in string.gmatch(event.parameter or "", "%S+") do
        table.insert(params, param)
    end

    local x = tonumber(params[1])
    local y = tonumber(params[2])
    local item_id = tonumber(params[3])
    local count = tonumber(params[4])

    local item_name = item_list[item_id]
    if not item_name then
        game.print("Invalid Item ID!")
        return
    end

    -- Finde AI Character
    local ai_characters = surface.find_entities_filtered{
        name = "character",
        force = "AI"
    }

    local character = ai_characters[1]

    if insert_exclude[recipe_id] then
        game.print("Item ID " .. recipe_id .. " cannot be inserted!")
        return
    end

    -- Prüfe ob Character das Item hat
    if character.get_item_count(item_name) == "none"
    then
        game.print("char has no " .. item_name .. "!")
        return
    end
    local item_count = character.get_item_count(item_name)
    if item_count < count then
        game.print("char has " .. item_count .. "x " .. item_name .. "!")
        return
    end

    -- Finde Maschine an der Position
    local entities = surface.find_entities_filtered{
        position = {x, y},
        radius = 0.5
    }

    if #entities == 0 then
        game.print("no machine found at (" .. x .. ", " .. y .. ")")
        return
    end

    local machine = entities[1]
    if machine.name == "character" then
        game.print("Cannot insert into character!")
        return
    end
    -- Prüfe ob die Entity ein Inventar hat
    if not machine.get_inventory(defines.inventory.furnace_source) and
       not machine.get_inventory(defines.inventory.assembling_machine_input) and
       not machine.get_inventory(defines.inventory.chest) then
        game.print(machine.name .. " no inventory to fill")
        return
    end

    -- Versuche in verschiedene Inventar-Typen einzufügen
    local inserted = 0

    -- Furnace Input
    local furnace_inv = machine.get_inventory(defines.inventory.furnace_source)
    if furnace_inv then
        inserted = furnace_inv.insert{name = item_name, count = count}
    end

    -- Assembling Machine Input
    if inserted == 0 then
        local assembly_inv = machine.get_inventory(defines.inventory.assembling_machine_input)
        if assembly_inv then
            inserted = assembly_inv.insert{name = item_name, count = count}
        end
    end

    -- Chest/Container
    if inserted == 0 then
        local chest_inv = machine.get_inventory(defines.inventory.chest)
        if chest_inv then
            inserted = chest_inv.insert{name = item_name, count = count}
        end
    end

    if inserted > 0 then
        -- Entferne Items aus Character Inventar
        character.remove_item{name = item_name, count = inserted}
        game.print("char has " .. inserted .. "x " .. item_name .. " in " .. machine.name .. " inserted")
    else
        game.print("insertfailed")
    end
end)

--change recipe of a machine
--/c_recipe x y <itemindex(1-52)>
commands.add_command("c_recipe", "Set recipe in machine: /c_recipe <x> <y> <recipe_id>", function(event)
    local surface = game.surfaces[1]

    -- Parse Parameters
    local params = {}
    for param in string.gmatch(event.parameter or "", "%S+") do
        table.insert(params, param)
    end

    local x = tonumber(params[1])
    local y = tonumber(params[2])
    local recipe_id = tonumber(params[3])

    if not x or not y or not recipe_id then
        game.print("Invalid syntax. Use: /c_recipe <x> <y> <recipe_id>")
        return
    end

    -- Check excluded/invalid recipes
    if recipe_exclude[recipe_id] then
        game.print("Item ID " .. recipe_id .. " is not a recipe!")
        return
    end

    local recipe_name = item_list[recipe_id]
    if not recipe_name then
        game.print("Invalid Recipe ID!")
        return
    end

    -- 1. Use the filter to Find ONLY Assembling Machines
    -- This prevents picking up belts, inserters, or items on the ground
    local entities = surface.find_entities_filtered{
        position = {x, y},
        radius = 0.5,
        type = "assembling-machine"
    }

    if #entities == 0 then
        game.print("No Assembling Machine found at (" .. x .. ", " .. y .. ")")
        return
    end

    local machine = entities[1]

    -- 2. Set the recipe using the Property, not the Function
    -- This is the API-safe way to do it. It won't crash C++.
    machine.recipe = recipe_name

    -- 3. Verify it worked
    -- machine.recipe returns the LuaRecipe object if successful, or nil if failed
    if machine.recipe and machine.recipe.name == recipe_name then
        game.print("Recipe " .. recipe_name .. " set in " .. machine.name .. " at (" .. x .. ", " .. y .. ")")
    else
        game.print("Recipe '" .. recipe_name .. "' is incompatible with " .. machine.name)
    end
end)

--take all items out of a machine
--/take x y
commands.add_command("take", "Take items from machine: /take <x> <y>", function(event)
    --local player = game.players[event.player_index]
    local surface = game.surfaces[1]

    -- Parse Parameter
    local params = {}
    for param in string.gmatch(event.parameter or "", "%S+") do
        table.insert(params, param)
    end

    local x = tonumber(params[1])
    local y = tonumber(params[2])

    --find the character
    local characters = surface.find_entities_filtered{
        name = "character",
        force = "AI"
    }

    local character = characters[1]

    -- Finde Maschine an der Position
    local entities = surface.find_entities_filtered{
        position = {x, y},
        radius = 0.5
    }

    if #entities == 0 then
        game.print("No machine at (" .. x .. ", " .. y .. ") found!")
        return
    end

    local machine = entities[1]
    if machine.name == "character" then
        game.print("Cannot take items from character!")
        return
    end
    -- Liste aller möglichen Inventar-Typen
    local inventory_types = {
        defines.inventory.chest,
        defines.inventory.furnace_result,
        defines.inventory.furnace_source,
        defines.inventory.assembling_machine_output,
        defines.inventory.assembling_machine_input,
        defines.inventory.lab_input,
        defines.inventory.fuel,
    }

    local items_taken = false

    for _, inv_type in pairs(inventory_types) do
        local inventory = machine.get_inventory(inv_type)

        if inventory and not inventory.is_empty() then
            for i = 1, #inventory do
                local stack = inventory[i]
                if stack.valid_for_read then
                    local item_name = stack.name
                    local item_count = stack.count


                    local inserted = character.insert{name = item_name, count = item_count}

                    if inserted > 0 then
                        stack.clear()
                        game.print("Took " .. inserted .. "x " .. item_name .. " from " .. machine.name)
                        items_taken = true
                    end
                end
            end
        end
    end

    if not items_taken then
        game.print("No items found in " .. machine.name .. " at (" .. x .. ", " .. y .. ")")
    end
end)

commands.add_command("resetsurface", "", function(event)
    game.delete_surface("Test Surface")
end)

commands.add_command("reset", "", function(event)
    local surface = game.surfaces[1]
    --local nauvis_settings = game.surfaces["nauvis"].map_gen_settings

    -- Ändere den Seed in den Settings
    --local new_seed = math.random(1, 4294967295)
    --nauvis_settings.seed = new_seed
    --nauvis_settings.peaceful_mode = true
    --nauvis_settings.no_enemies_mode = true
    --nauvis_settings.cliff_settings = {richness = 0}
    --nauvis_settings.height = 1000
    --nauvis_settings.width = 1000
    --nauvis_settings.starting_area = 3
    --
    --
    ---- Erstelle die neue Surface mit den modifizierten Nauvis-Settings
    --local surface = game.create_surface("Test Surface", nauvis_settings)

    surface.request_to_generate_chunks({0, 0}, 4)
    surface.force_generate_chunk_requests()

    local types = {
        "assembling-machine",
        "furnace",
        "mining-drill",
        "transport-belt",
        "underground-belt",
        "chemical-plant",
        "inserter",
        "boiler",
        "generator",
        "oil-refinery",
        "lab",
        "offshore-pump",
        "pipe",
        "pipe-to-ground",
        "electric-pole",
        "splitter",
        "pump"
    }

    -- Delete all AI entities (optional, currently commented)
    --for _, type in pairs(types) do
    --    for _, entity in pairs(surface.find_entities_filtered{type = type, force = "AI"}) do
    --        entity.destroy()
    --    end
    --end

    -- Delete AI characters
    for _, entity in pairs(surface.find_entities_filtered{name = "character", force = "AI"}) do
        entity.die()
    end

    -- Delete corpses
    for _, corpse in pairs(surface.find_entities_filtered{type = "character-corpse"}) do
        corpse.destroy()
    end

    -- Set game speed
    game.speed = 4

    -- Spawn new AI character
    surface.create_entity{
        name = "character",
        position = {x = 0, y = 0},
        force = "AI"
    }

    -- Reset AI Force techs and queue
    local force = game.forces["AI"]
    if force then
        -- Reset AI research index
        ai_research_index = 1

        -- Empty research queue
        force.research_queue = {}

        -- Reset all techs
        for _, tech in pairs(force.technologies) do
            tech.researched = false
        end

        -- Set starting techs researched
        local starting_techs = {
            "electronics",
            "steam-power",
            "automation-science-pack"
        }
        for _, tech_name in pairs(starting_techs) do
            local tech = force.technologies[tech_name]
            if tech then
                tech.researched = true
            end
        end

        -- Start first AI research from the predefined list, skip starting techs
        while ai_research_index <= #AI_RESEARCH_QUEUE do
            local first_tech_name = AI_RESEARCH_QUEUE[ai_research_index]
            local tech = force.technologies[first_tech_name]

            if tech and not tech.researched and not table.contains(starting_techs, first_tech_name) then
                force.add_research(tech)
                force.print("AI reset complete. First tech queued: " .. first_tech_name)
                ai_research_index = ai_research_index + 1
                break
            end

            ai_research_index = ai_research_index + 1
        end
    else
        game.print("AI force not found!")
    end
end)

-- Helper function to check if a table contains a value
function table.contains(tbl, val)
    for _, v in pairs(tbl) do
        if v == val then return true end
    end
    return false
end

commands.add_command("speed", "", function(event)
    if event.parameter then
        game.speed = tonumber(event.parameter)
        game.print("Game speed set to: " .. game.speed)
    else
        game.print("Current game speed: " .. game.speed)
    end
end)

commands.add_command("jimbo_button", "", function(event)
    local player = game.players[event.player_index]

    if player.gui.top.camera_button then
        player.gui.top.camera_button.destroy()
    else
        local button = player.gui.top.add{
            type = "button",
            name = "Jimbo_button",
            caption = "Jimbo Cam"
        }
    end
end)

script.on_event(defines.events.on_gui_click, function(event)
    if event.element.name == "Jimbo_button" then
        local player = game.players[event.player_index]
        local surface = game.surfaces[1]

        local bot = surface.find_entities_filtered{name="character", force="AI"}[1]

        if bot then
            if player.gui.left.camera_frame then
                player.gui.left.camera_frame.destroy()
            else
                local frame = player.gui.left.add{
                    type = "frame",
                    name = "camera_frame",
                    caption = "Jimbo Camera",
                    direction = "vertical"
                }

                local camera = frame.add{
                    type = "camera",
                    name = "Jimbo_camera",
                    position = bot.position,
                    surface_index = 1,
                    zoom = 0.75
                }

                camera.style.minimal_width = 300
                camera.style.minimal_height = 300

                if bot.valid then
                    camera.entity = bot
                end
            end
        else
            player.print("Kein AI-Bot gefunden!")
        end
    end
end)

commands.add_command("ai_r", "Add technology to AI research queue", function(event)
  local tech_name = event.parameter
  if not tech_name or tech_name == "" then
    game.print("Usage: /ai_research <technology_name>")
    return
  end

  local force = game.forces["AI"]
  if not force then
    game.print("Force 'AI' not found")
    return
  end

  local tech = force.technologies[tech_name]
  if tech and not tech.researched then
    force.add_research(tech_name)
    game.print("Technology '" .. tech_name .. "' added to AI research queue")
  elseif tech and tech.researched then
    game.print("Technology '" .. tech_name .. "' is already researched")
  else
    game.print("Technology '" .. tech_name .. "' not found")
  end
end)

-- Command: fill_queue (sicher)
commands.add_command("fill_queue", "Fill AI research queue with next 5 technologies.", function(event)
    local force = game.forces["AI"]
    if not force then
        game.print("Force 'AI' not found")
        return
    end

    local added_count = 0
    while added_count < 1 and ai_research_index <= #AI_RESEARCH_QUEUE do
        local tech_name = AI_RESEARCH_QUEUE[ai_research_index]
        local tech = force.technologies[tech_name]

        if tech and not tech.researched then
            force.add_research(tech)
            added_count = added_count + 1
            game.print("Added to AI queue: " .. tech_name)
        end

        ai_research_index = ai_research_index + 1
    end

    game.print("Added " .. added_count .. " technologies to AI queue.")
end)

-- Event: on_research_finished (bereits korrekt, bleibt)
script.on_event(defines.events.on_research_finished, function(event)
    local tech = event.research
    local force = tech.force
    if force.name ~= "AI" then return end

    -- Wenn die Tech in der Startliste ist, nichts tun
    if AI_START_TECHS[tech.name] then
        force.print("Skipped AI research trigger for start tech: " .. tech.name)
        return
    end

    -- Füge genau 1 Tech aus der Liste hinzu
    local added_count = 0
    while added_count < 1 and ai_research_index <= #AI_RESEARCH_QUEUE do
        local next_tech_name = AI_RESEARCH_QUEUE[ai_research_index]
        local next_tech = force.technologies[next_tech_name]

        if next_tech and not next_tech.researched then
            force.add_research(next_tech)
            added_count = 1
            force.print("Added next AI research: " .. next_tech_name)
        end

        ai_research_index = ai_research_index + 1
    end
end)

commands.add_command("reset_ai_index", "Reset AI research index to start of the list.", function(event)
    ai_research_index = 1
    game.print("AI research index reset to 1.")
end)