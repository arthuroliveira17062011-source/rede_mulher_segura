import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { createClient } from '@supabase/supabase-js';

// Carrega as variáveis do arquivo .env
dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middlewares essenciais
app.use(cors());
app.use(express.json());

// Inicialização do Cliente Supabase
const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error("ERRO: As variáveis SUPABASE_URL e SUPABASE_KEY precisam estar configuradas no .env");
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

// Rota de teste
app.get('/', (req, res) => {
  res.json({ message: 'API rodando com sucesso!' });
});

// -------------------------------------------------------------
// ROTA GET: Listar registros do banco de dados
// -------------------------------------------------------------
app.get('/api/items', async (req, res) => {
  try {
    const { data, error } = await supabase
      .from('items')
      .select('*')
      .order('id', { ascending: false });

    if (error) {
      return res.status(400).json({ error: error.message });
    }

    return res.status(200).json(data);
  } catch (err) {
    return res.status(500).json({ error: 'Erro interno no servidor ao buscar itens.' });
  }
});

// -------------------------------------------------------------
// ROTA POST: Inserir novo registro no banco de dados
// -------------------------------------------------------------
app.post('/api/items', async (req, res) => {
  try {
    const { title, description } = req.body;

    if (!title) {
      return res.status(400).json({ error: 'O campo "title" é obrigatório.' });
    }

    const { data, error } = await supabase
      .from('items')
      .insert([{ title, description }])
      .select();

    if (error) {
      return res.status(400).json({ error: error.message });
    }

    return res.status(201).json(data[0]);
  } catch (err) {
    return res.status(500).json({ error: 'Erro interno no servidor ao criar item.' });
  }
});

// Inicialização do servidor HTTP
app.listen(PORT, () => {
  console.log(`Servidor rodando em http://localhost:${PORT}`);
});