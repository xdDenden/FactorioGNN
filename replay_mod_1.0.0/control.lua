local player_info_fields = {"inventory", "x", "y", "current_step", "current_tech"}
local mask_fields = {"moveto", "mine", "craft", "build", "insert_into", "take", "change_recipe"}

local function create_replay_gui(player)
    if player.gui.screen.replay_gui then return end

    local frame = player.gui.screen.add{
        type = "frame",
        name = "replay_gui",
        caption = "Mein Fenster",
        direction = "vertical",
    }
    frame.location = {x = 700, y = 900}

    -- 1. Status-Bereich für Aktionen
    local status_grid = frame.add{
        type = "table",
        column_count = 4 -- Label | Wert | Label | Wert
    }

    status_grid.add{type = "label", caption = "Last Action = "}
    status_grid.add{
        type = "label",
        name = "replay_last_action",
        caption = "None",
        style = "bold_label"
    }

    status_grid.add{type = "label", caption = "  |  Next Action = "}
    status_grid.add{
        type = "label",
        name = "replay_next_action",
        caption = "None",
        style = "bold_label"
    }

    -- Trennlinie oder Platzhalter
    frame.add{type = "line", direction = "horizontal"}

    -- 2. Button-Bereich (dein bestehender Code)
    local grid = frame.add{
        type = "table",
        name = "button_grid",
        column_count = 3
    }

    grid.add{ type = "button", name = "my_left_arrow_button", caption = "◄" }
    grid.add{ type = "button", name = "my_up_arrow_button", caption = "=" }
    grid.add{ type = "button", name = "my_right_arrow_button", caption = "►" }
end

local function create_mask_gui(player)
    if player.gui.screen.mask_gui then return end
    local frame = player.gui.screen.add{
        type = "frame",
        name = "mask_gui",
        caption = "Current Framemask",
        direction = "vertical",
    }
    frame.location = {x = 1000, y = 120}
    local grid = frame.add{type = "table", name = "mask_grid", column_count = 7}

    local cats = {"moveto", "mine", "craft", "build", "insert_into", "take", "change_recipe"}
    for _, v in ipairs(cats) do
        grid.add{type = "label", caption = v, style = "bold_label"}
    end
    for i = 1, #cats do
        grid.add{type = "label", name = "maskval_" .. i, caption = "0"}
    end
end

local function create_playerinfo_gui(player)
    if player.gui.screen.playerinfo_gui then return end
    local frame = player.gui.screen.add{
        type = "frame",
        name = "playerinfo_gui",
        caption = "Current Player Info",
        direction = "vertical",
    }
    frame.location = {x = 0, y = 10}
    local grid = frame.add{type = "table", name = "info_grid", column_count = 2}

    local fields = {"Inventory", "X", "Y", "Current Step", "Current Tech"}
    for _, name in ipairs(fields) do
        grid.add{type = "label", caption = name .. ":"}
        grid.add{
            type = "label",
            name = "playerinfo_" .. name:gsub(" ", "_"):lower(),
            caption = "0"
        }
    end
end

script.on_init(function()
  for _, player in pairs(game.players) do
    create_replay_gui(player)
    create_mask_gui(player)
    create_playerinfo_gui(player)
  end
end)

script.on_event(defines.events.on_player_created, function(event)
  local player = game.get_player(event.player_index)
  create_replay_gui(player)
  create_mask_gui(player)
  create_playerinfo_gui(player)
end)

script.on_event(defines.events.on_gui_click, function(event)
  if not event.element then return end

  if event.element.name == "my_center_button" then
    game.print("zzz")
  elseif event.element.name == "my_left_arrow_button" then
    game.print("Links!")
  elseif event.element.name == "my_up_arrow_button" then
    game.print("Hoch!")
  elseif event.element.name == "my_right_arrow_button" then
    game.print("Rechts!")
  elseif event.element.name == "my_down_arrow_button" then
    game.print("Runter!")
  end
end)

commands.add_command("update_gui", "Update Info Panel", function(event)
    local player = game.get_player(event.player_index)
    if not (player and event.parameter) then return end
    local grid = player.gui.screen.playerinfo_gui.info_grid
    local fields = {"inventory", "x", "y", "current_step", "current_tech"}
    local i = 1
    for val in event.parameter:gmatch("%S+") do
        if fields[i] then
            local lbl = grid["playerinfo_" .. fields[i]]
            if lbl then lbl.caption = tostring(val) end
        end
        i = i + 1
    end
end)

commands.add_command("update_mask", "Update Mask Panel", function(event)
    local player = game.get_player(event.player_index)
    if not (player and event.parameter) then return end
    local grid = player.gui.screen.mask_gui.mask_grid
    local i = 1
    for val in event.parameter:gmatch("%S+") do
        local lbl = grid["maskval_" .. i]
        if lbl then lbl.caption = tostring(val) end
        i = i + 1
    end
end)