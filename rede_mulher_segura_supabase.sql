-- ============================================================
-- REDE MULHER SEGURA — Banco de Dados Completo (Supabase)
-- ============================================================

-- 0. LIMPEZA PREVENTIVA (Apaga tabelas antigas se existirem)
drop table if exists public.item_pedido cascade;
drop table if exists public.pedido cascade;
drop table if exists public.produto cascade;
drop table if exists public.configuracoes_de_seguranca cascade;
drop table if exists public.ocorrencias_de_alerta cascade;
drop table if exists public.contato_emergencia cascade;
drop table if exists public.usuaria cascade;

create extension if not exists "pgcrypto";

-- ------------------------------------------------------------
-- 1. USUARIA (Vinculada à autenticação do Supabase)
-- ------------------------------------------------------------
create table public.usuaria (
    id_usuario           uuid primary key references auth.users(id) on delete cascade,
    nome_completo        text not null,
    cpf                  text not null unique,
    email                text not null unique,
    telefone_celular      text not null unique,
    data_nascimento      date not null,
    endereco_residencia  text,
    frase_chave          text,
    criado_em             timestamptz not null default now()
);

comment on table public.usuaria is 'Dados cadastrais da usuária do aplicativo';
comment on column public.usuaria.frase_chave is 'Frase-comando usada para ativar o alerta por voz';

-- ------------------------------------------------------------
-- 2. CONTATO_EMERGENCIA
-- ------------------------------------------------------------
create table public.contato_emergencia (
    id_contato              uuid primary key default gen_random_uuid(),
    id_usuario              uuid not null references public.usuaria (id_usuario) on delete cascade,
    nome_completo           text not null,
    telefone_whatsapp       text not null,
    prioridade_notificacao integer not null,
    criado_em               timestamptz not null default now()
);

comment on table public.contato_emergencia is 'Contatos de confiança que recebem o alerta de socorro';

-- ------------------------------------------------------------
-- 3. OCORRENCIAS_DE_ALERTA
-- ------------------------------------------------------------
create table public.ocorrencias_de_alerta (
    id_alerta                    uuid primary key default gen_random_uuid(),
    id_usuario                   uuid not null references public.usuaria (id_usuario) on delete cascade,
    data_hora_ativacao           timestamptz not null default now(),
    tipo_ativacao                text not null check (tipo_ativacao in ('botao', 'comando_voz', 'temporizador')),
    link_google_maps_localizacao text,
    link_compartilhamento        text
);

comment on table public.ocorrencias_de_alerta is 'Registro de cada vez que o alerta de socorro foi ativado';

-- ------------------------------------------------------------
-- 4. CONFIGURACOES_DE_SEGURANCA
-- ------------------------------------------------------------
create table public.configuracoes_de_seguranca (
    id_configuracao             uuid primary key default gen_random_uuid(),
    id_usuario                  uuid not null unique references public.usuaria (id_usuario) on delete cascade,
    tempo_temporizador_segundo  integer,
    pin_desativado               text,
    tema_disfarce_padrao        text default 'cardapio_restaurante'
);

comment on table public.configuracoes_de_seguranca is 'Preferências de segurança e disfarce definidas pela usuária';

-- ------------------------------------------------------------
-- 5. CAMADA DE DISFARCE (CARDÁPIO / PEDIDOS)
-- ------------------------------------------------------------
create table public.produto (
    id_produto   uuid primary key default gen_random_uuid(),
    nome         text not null,
    descricao    text,
    preco        numeric(10,2) not null,
    categoria    text not null check (categoria in ('comida', 'bebida', 'sobremesa')),
    url_imagem   text,
    disponivel   boolean default true,
    criado_em    timestamptz not null default now()
);

create table public.pedido (
    id_pedido    uuid primary key default gen_random_uuid(),
    id_usuario   uuid references public.usuaria(id_usuario) on delete cascade,
    valor_total  numeric(10,2) not null,
    status       text default 'recebido',
    criado_em    timestamptz not null default now()
);

create table public.item_pedido (
    id_item      uuid primary key default gen_random_uuid(),
    id_pedido    uuid not null references public.pedido(id_pedido) on delete cascade,
    id_produto   uuid not null references public.produto(id_produto),
    quantidade   integer not null check (quantidade > 0),
    preco_unit   numeric(10,2) not null
);

-- ------------------------------------------------------------
-- ÍNDICES ÚTEIS
-- ------------------------------------------------------------
create index idx_contato_emergencia_usuario on public.contato_emergencia (id_usuario);
create index idx_ocorrencias_usuario on public.ocorrencias_de_alerta (id_usuario);

-- ------------------------------------------------------------
-- ROW LEVEL SECURITY (RLS) E POLÍTICAS DE SEGURANÇA
-- ------------------------------------------------------------
alter table public.usuaria enable row level security;
alter table public.contato_emergencia enable row level security;
alter table public.ocorrencias_de_alerta enable row level security;
alter table public.configuracoes_de_seguranca enable row level security;
alter table public.produto enable row level security;
alter table public.pedido enable row level security;
alter table public.item_pedido enable row level security;

-- Usuária
create policy "usuaria_ve_apenas_seus_dados" on public.usuaria for select using (auth.uid() = id_usuario);
create policy "usuaria_atualiza_apenas_seus_dados" on public.usuaria for update using (auth.uid() = id_usuario);
create policy "usuaria_insere_proprio_perfil" on public.usuaria for insert with check (auth.uid() = id_usuario);

-- Segurança e Alertas
create policy "contato_emergencia_por_usuaria" on public.contato_emergencia for all using (auth.uid() = id_usuario);
create policy "ocorrencias_por_usuaria" on public.ocorrencias_de_alerta for all using (auth.uid() = id_usuario);
create policy "configuracoes_por_usuaria" on public.configuracoes_de_seguranca for all using (auth.uid() = id_usuario);

-- Disfarce (Cardápio público para leitura, pedidos por usuária)
create policy "produtos_visiveis_para_todos" on public.produto for select using (true);
create policy "pedidos_por_usuaria" on public.pedido for all using (auth.uid() = id_usuario);
create policy "itens_pedido_por_usuaria" on public.item_pedido for all 
    using (exists (select 1 from public.pedido where public.pedido.id_pedido = public.item_pedido.id_pedido and public.pedido.id_usuario = auth.uid()));
