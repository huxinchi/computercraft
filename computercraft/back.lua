local _py = {
    url = '__url__',
    proto_version = 5,
    event_sub = {},
    tasks = {},
    filters = {},
    coparams = {},
    modules = {},
    mcache = {},
    temp = {},
    luaobjs = {},
    next_luaobjid = 1,
    password = "__password__",
    waiting_py = {},
    next_pycall_id = 1,
    pyfunc_reverse = {},
    pyside=false
}
log=fs.open("log.log","w")
if log == nil then 
  error("not can open log file")
end
function checkandwrite(str)
  if fs.getFreeSpace("/")<=1024 then
    fs.delete("log.log")
    log=fs.open("log.log","w")
    if log == nil then 
      error("not can open log file")
    end
  end
  log.write(str)
  log.flush()
end

if type(_G) == 'table' then
    _py.genv = _G 
elseif type(_ENV) == 'table' then
    _py.genv = _ENV
else
    error('E001: Can\'t get environment')
end
_py.genv.temp = _py.temp
_py.genv._m = _py.modules
_py.genv._py = _py
if type(loadstring) == 'function' then
    -- 5.1: prefer loadstring
    function _py.loadstring(source)
        local r, err = loadstring(source)
        if r ~= nil then setfenv(r, _py.genv) end
        return r, err
    end
else
    -- 5.2+: load can deal with strings as well
    function _py.loadstring(source)
        return load(source, nil, nil, _py.genv)
    end
end
function _py.handle_coro_result(task_id, r)
    if coroutine.status(_py.tasks[task_id]) == 'dead' then
        _py.ws_send('T', task_id, _py.serialize(r))
        _py.drop_task(task_id)
        return
    end
    if r[1] ~= true then
        _py.filters[task_id] = nil
        return
    end
    local flt = r[2]
    if type(flt) == 'table' and flt.__pyop__ then
        local call_id = _py.next_pycall_id
        _py.next_pycall_id = call_id + 1
        _py.waiting_py[call_id] = task_id
        _py.filters[task_id] = {"fuck event"}
        _py.ws_send('P',
            call_id,
            {
                fid = flt.__pyop__,
                op = flt.op,
                args = flt.args,
        })
    else
        _py.filters[task_id] = flt
    end
end

function _py.loadmethod(code)
    -- 0..N  R:module:   -- require(module)
    -- 0..1  G:module:   -- use builtin module
    -- choice:
    --   M:method$   -- take method of loaded module
    --   code$       -- arbitrary code
    if _py.mcache[code] ~= nil then return _py.mcache[code] end

    local mod, modname
    while true do
        local _, _, rmod, mcode = string.find(code, '^R:([%a%w_%.]+):(.*)$')
        if rmod == nil then break end
        if _py.modules[rmod] == nil then
            local r, v = pcall(require, rmod)
            if not r then return nil, 'module not found' end
            _py.modules[rmod] = v
        end
        mod, code = _py.modules[rmod], mcode
    end
    do
        local _, _, rmod, mcode = string.find(code, '^G:([%a%w_%.]+):(.*)$')
        if rmod ~= nil then
            mod, code = _py.genv[rmod], mcode
            if mod == nil then return nil, 'module not found' end
        end
    end

    local fn
    do

local _, _, meth = string.find(code, '^M:([%a%w_%.]+)$')
        if meth ~= nil then
            fn = mod[meth]
            if fn == nil then return nil, 'method not found' end
        else
            local err
            fn, err = _py.loadstring(code)
            if not fn then return nil, err end
        end
    end
    _py.mcache[code] = fn
    return fn
end

if type(os) == 'table' and type(os.pullEventRaw) == 'function' then
    _py.pullEvent = os.pullEventRaw  -- computercraft, preferrable
elseif type(os) == 'table' and type(os.pullEvent) == 'function' then
    _py.pullEvent = os.pullEvent  -- computercraft
else
    error('E002: Can\'t detect pullEvent method')
end
if type(arg) == 'table' then
    _py.argv = arg
else
    _py.argv = {...}
end

-- 移除 --pyside 并紧凑化 argv（去掉 index 空洞）
do
    local new_argv = {}
    new_argv[0] = _py.argv[0]
    local n = 1
    local i = 1
    while _py.argv[i] ~= nil do
        if _py.argv[i] == '--pyside' then
            _py.pyside = true
        else
            new_argv[n] = _py.argv[i]
            n = n + 1
        end
        i = i + 1
    end
    _py.argv = new_argv
end

do
    local function s_rec(v, ctx)
        local t = type(v)
        if v == nil then
            return 'N'
        elseif v == false then
            return 'F'
        elseif v == true then
            return 'T'
        elseif t == 'number' then
            return '[' .. tostring(v) .. ']'
        elseif t == 'string' then
            return string.format('<%u>', #v) .. v
        elseif t == 'function' then
            local orig = _py.pyfunc_reverse[v]
            if orig then
                return 'P[' .. orig .. ']'
            end
            local id = _py.next_luaobjid
            _py.next_luaobjid = id + 1
            _py.luaobjs[id] = v
            return 'K[' .. id .. ']'
        elseif t == 'thread' then
            local id = _py.next_luaobjid
            _py.next_luaobjid = id + 1
            _py.luaobjs[id] = v
            return 'Y[' .. id .. ']'
        elseif t == 'userdata' then
            local id = _py.next_luaobjid
            _py.next_luaobjid = id + 1
            _py.luaobjs[id] = v
            return 'O[' .. id .. ']'
        elseif t == 'table' then
            local mt = getmetatable(v)
            if mt and mt.__cc_pyobj_id then
                return 'I' .. _py.serialize(
                    {fid = mt.__cc_pyobj_id, keys = {}})
            end
            if mt ~= nil then
                local id = _py.next_luaobjid
                _py.next_luaobjid = id + 1
                _py.luaobjs[id] = v
                return 'O[' .. id .. ']'
            end
            -- 无 metatable → 检查是否已经展开过
            local existing = ctx.ids[v]
            if existing then
                return 'R[' .. existing .. ']'
            end
            local my_id = ctx.next
            ctx.next = my_id + 1
            ctx.ids[v] = my_id
            local r = '{'
            for k, x in pairs(v) do
                r = r .. ':' .. s_rec(k, ctx) .. s_rec(x, ctx)
            end
            return r .. '}'
        else
            error('Cannot serialize type ' .. t, 0)
        end
    end

    _py.serialize = function(v)
        return s_rec(v, {ids = {}, next = 1})
    end
end

function _py.create_stream(s, idx)
    if idx == nil then idx = 1 end
    return {
        getidx=function() return idx end,
        isend=function() return idx > #s end,
        fixed=function(n)
            local r = s:sub(idx, idx + n - 1)
            if #r ~= n then error('Unexpected end of stream') end
            idx = idx + n
            return r
        end,
        tostop=function(sym)
            local newidx = s:find(sym, idx, true)
            if newidx == nil then error('Unexpected end of stream') end
            local r = s:sub(idx, newidx - 1)
            idx = newidx + 1
            return r
        end,
    }
end

local function deserialize_rec(stream, ctx)
    local tok = stream.fixed(1)
    if tok == 'N' then
        return nil
    elseif tok == 'K' then
        stream.fixed(1)
        local id = tonumber(stream.tostop(']'))
        return _py.luaobjs[id]
    elseif tok == 'Y' then
        stream.fixed(1)
        local id = tonumber(stream.tostop(']'))
        return _py.luaobjs[id]
    elseif tok == 'O' then
        stream.fixed(1)
        local id = tonumber(stream.tostop(']'))
        return _py.luaobjs[id]
    elseif tok == 'R' then
        stream.fixed(1)
        local ref = tonumber(stream.tostop(']'))
        local obj = ctx.building[ref]
        if obj == nil then
            error('R[' .. ref .. ']: invalid ref')
        end
        return obj
    elseif tok == 'F' then
        return false
    elseif tok == 'T' then
        return true
    elseif tok == '[' then
        return tonumber(stream.tostop(']'))
    elseif tok == '<' then
        local slen = tonumber(stream.tostop('>'))
        return stream.fixed(slen)
    elseif tok == 'E' then
        local slen = tonumber(stream.tostop('>'))
        local fn = assert(_py.loadstring(stream.fixed(slen)))
        return fn()
    elseif tok == 'X' then
        local slen = tonumber(stream.tostop('>'))
        local key = stream.fixed(slen)
        return _py.temp[key]
    elseif tok == '{' then
        local ref = ctx.next
        ctx.next = ref + 1
        local r = {}
        ctx.building[ref] = r
        while true do
            tok = stream.fixed(1)
            if tok == ':' then
                local key = deserialize_rec(stream, ctx)
                r[key] = deserialize_rec(stream, ctx)
            else
                break
            end
        end
        return r
    elseif tok == 'P' then
        stream.fixed(1)
        local fid = tonumber(stream.tostop(']'))
        local fn = function(...)
            return coroutine.yield({
                __pyop__ = fid,
                op = 'call',
                args = {...},
            })
        end
        _py.pyfunc_reverse[fn] = fid
        return fn
    elseif tok == 'I' then
        local spec = deserialize_rec(stream, ctx)
        spec.mt.__cc_pyobj_id = spec.fid
        return setmetatable({_fid = spec.fid}, spec.mt)
    else
        error('Unknown token ' .. tok)
    end
end

function _py.deserialize(stream)
    return deserialize_rec(stream, {building = {}, next = 1})
end

function _py.drop_task(task_id)
    _py.tasks[task_id] = nil
    _py.filters[task_id] = nil
    _py.coparams[task_id] = nil
end

-- nil-safe
if type(table.maxn) == 'function' then
    function _py.safe_unpack(a)
        return table.unpack(a, 1, table.maxn(a))
    end
else
    function _py.safe_unpack(a)
        local maxn = #a
        for k in pairs(a) do
            if type(k) == 'number' and k > maxn then maxn = k end
        end
        return table.unpack(a, 1, maxn)
    end
end

if type(http) == 'table' and type(http.websocket) == 'function' then
    function _py.start_connection()
        local ws = http.websocket(_py.url)
        if not ws then
            error('Unable to connect to server ' .. _py.url)
        end
        _py.ws = {
            send = function(m) return ws.send(m, true) end,
            close = function() ws.close() end,
        }
    end
else
    error('E003: Can\'t detect connection method')
end

function _py.ws_send(action, ...)
    local m = action
    for _, v in ipairs({...}) do
        m = m .. _py.serialize(v)
    end
    checkandwrite("send:"..m.."\n")
    _py.ws.send(m)
end

function _py.exec_python_directive(dstring)
    checkandwrite("recv:"..dstring.."\n")
    local msg = _py.create_stream(dstring)
    local action = msg.fixed(1)

    if action == 'T' or action == 'I' then  -- new task
        local task_id = _py.deserialize(msg)
        local code = _py.deserialize(msg)
        local params = _py.deserialize(msg)

        local fn, err = _py.loadmethod(code)
        if fn == nil then
            -- couldn't compile
            _py.ws_send('T', task_id, _py.serialize{false, err})
        else
            if action == 'I' then
                _py.ws_send('T', task_id, _py.serialize{fn(_py.safe_unpack(params))})
            else
                _py.tasks[task_id] = coroutine.create(fn)
                _py.coparams[task_id] = params
            end
        end
    elseif action == 'F' then  -- free refs
        local spec = _py.deserialize(msg)
        if spec.luaobjs then
            for _, id in ipairs(spec.luaobjs) do
                _py.luaobjs[id] = nil
            end
        end
        if spec.pyfuncs then
            local idset = {}
            for _, fid in ipairs(spec.pyfuncs) do
                idset[fid] = true
            end
            for fn, id in pairs(_py.pyfunc_reverse) do
                if idset[id] then
                    _py.pyfunc_reverse[fn] = nil
                end
            end
        end
    elseif action == 'D' then  -- drop tasks
        while not msg.isend() do
            _py.drop_task(_py.deserialize(msg))
        end
    elseif action == 'S' or action == 'U' then  -- (un)subscribe to event
        local event = _py.deserialize(msg)
        if action == 'S' then
            _py.event_sub[event] = true
        else
            _py.event_sub[event] = nil
        end
    elseif action == 'C' then  -- close session
        local err = _py.deserialize(msg)
        if err ~= nil then
            io.stderr:write(err .. '\n')
        end
        return true
    elseif action == 'R' then
         local call_id = _py.deserialize(msg)
         local ok = _py.deserialize(msg)
         local result = _py.deserialize(msg)
         local task_id = _py.waiting_py[call_id]
        _py.waiting_py[call_id] = nil
        if task_id and _py.tasks[task_id] then
            local r
            if ok then
                r = {coroutine.resume(_py.tasks[task_id], result)}
            else
                -- 失败：把 nil, err 传给用户代码，由用户决定处理
                r = {coroutine.resume(_py.tasks[task_id], nil, result)}
            end
            _py.handle_coro_result(task_id, r)
        end
    end
end
function _py.resume_coros(event, p1, p2, p3, p4, p5)
    for task_id in pairs(_py.tasks) do
        if _py.filters[task_id] == nil or _py.filters[task_id] == event then
            local r
            if _py.coparams[task_id] ~= nil then
                r = {coroutine.resume(
                    _py.tasks[task_id],
                    _py.safe_unpack(_py.coparams[task_id]))}
                _py.coparams[task_id] = nil
            else
                r = {coroutine.resume(
                    _py.tasks[task_id],
                    event, p1, p2, p3, p4, p5)}
            end
            _py.handle_coro_result(task_id, r)
        end
    end
end


    function _py.start_program(name)
        local path = fs.combine(shell.dir(), name)
        if not fs.exists(path) then return nil end
        if fs.isDir(path) then return nil end
        local f = fs.open(path, 'r')
        local code = f.readAll()
        f.close()
        return path, code
    end


_py.start_connection()
do
    local path, code = nil, nil
    if _py.argv[1] ~= nil and not _py.pyside then
        path, code = _py.start_program(_py.argv[1])
        if path == nil then error('Program not found') end
    end
    _py.ws_send('0',_py.password, _py.proto_version,_py.pyside ,_py.argv, path, code)
end
while true do
    local event, p1, p2, p3, p4, p5 = _py.pullEvent()
    if event == 'websocket_message' and p1==_py.url then
        if _py.exec_python_directive(p2) then break end
    elseif event == 'websocket_closed' and p1==_py.url then
        error('Connection with server has been closed')
    elseif event == 'websocket_failure' and p1==_py.url then
      error('WebSocket failure: ' .. tostring(p2))
    elseif event == 'terminate' then
        _py.ws_send('C')  -- trigger KeyboardInterrupt
    elseif _py.event_sub[event] == true or _py.event_sub['*'] == true then
    _py.ws_send('E', event, {p1, p2, p3, p4, p5})
    end
    _py.resume_coros(event, p1, p2, p3, p4, p5)
end
_py.ws.close()
log.close()
